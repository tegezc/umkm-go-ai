// File: mobile_app/lib/presentation/screens/chat_screen.dart

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:file_picker/file_picker.dart';
import '../../data/services/api_service.dart';
import '../../bloc/chat/chat_bloc.dart';

class ChatScreen extends StatelessWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => ChatBloc(apiService: ApiService()),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('UMKM-Go AI'),
          backgroundColor: Colors.blueAccent,
        ),
        body: Column(
          children: [
            Expanded(
              child: BlocBuilder<ChatBloc, ChatState>(
                builder: (context, state) {
                  if (state is ChatError && state.messages.isEmpty) {
                    return Center(child: Text('Error: ${state.error}'));
                  }
                  if (state.messages.isEmpty) {
                    return const Center(child: Text('Start conversation...'));
                  }
                  return ListView.builder(
                    padding: const EdgeInsets.all(8.0),
                    itemCount: state.messages.length,
                    itemBuilder: (context, index) {
                      final message = state.messages[index];
                      return _buildChatBubble(message);
                    },
                  );
                },
              ),
            ),
            BlocSelector<ChatBloc, ChatState, bool>(
              selector: (state) => state is ChatLoading,
              builder: (context, isLoading) {
                return isLoading
                    ? const Padding(
                  padding: EdgeInsets.all(8.0),
                  child: CircularProgressIndicator(),
                )
                    : const SizedBox.shrink();
              },
            ),
            const _InputArea(),
          ],
        ),
      ),
    );
  }

  Widget _buildChatBubble(ChatMessage message) {
    final alignment = message.type == MessageType.user
        ? Alignment.centerRight
        : Alignment.centerLeft;

    Color bubbleColor;
    Color textColor;
    switch (message.type) {
      case MessageType.user:
        bubbleColor = Colors.blue[300]!;
        textColor = Colors.white;
        break;
      case MessageType.ai:
        bubbleColor = Colors.grey[200]!;
        textColor = Colors.black87;
        break;
      case MessageType.loading:
        bubbleColor = Colors.grey[100]!;
        textColor = Colors.grey[600]!;
        break;
      case MessageType.error:
        bubbleColor = Colors.red[100]!;
        textColor = Colors.red[700]!;
        break;
    }

    return Align(
      alignment: alignment,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 5.0, horizontal: 8.0),
        padding: const EdgeInsets.all(12.0),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(15.0),
        ),
        //  Teks + image ---
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: textColor,
              ),
            ),
            if (message.type == MessageType.loading)
              const Padding(
                padding: EdgeInsets.only(top: 8.0),
                child: SizedBox(
                    width: 15,
                    height: 15,
                    child: CircularProgressIndicator(strokeWidth: 2)),
              ),
            // Tampilkan gambar HANYA jika imageUrl ada DAN tidak kosong
            if (message.imageUrl != null && message.imageUrl!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Image.network(
                  message.imageUrl!,
                  width: 200,
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) return child;
                    return const Center(child: CircularProgressIndicator());
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return const Text(' Failed to load image', style: TextStyle(color: Colors.red));
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _InputArea extends StatefulWidget {
  const _InputArea();

  @override
  State<_InputArea> createState() => _InputAreaState();
}

class _InputAreaState extends State<_InputArea> {
  final TextEditingController _textController = TextEditingController();

  void _sendMessage() {
    final query = _textController.text;
    if (query.isNotEmpty) {
      context.read<ChatBloc>().add(SendTextMessageEvent(query));
      _textController.clear();
    }
  }

  Future<void> _pickAndAnalyzeFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
        withData: true,
      );

      if (!mounted) return;

      if (result != null && result.files.single.bytes != null) {
        context.read<ChatBloc>().add(AnalyzeFileEvent(result.files.single));
      } else {
        print("Pemilihan file dibatalkan.");
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error selecting file")),
      );
    }
  }

  Future<void> _pickAndGenerateBrandKit() async {
    try {
      // Filter HANYA untuk Gambar
      final result = await FilePicker.platform.pickFiles(
        type: FileType.image,
      );
      if (!mounted) return;

      final file = result?.files.single;
      if (file != null) {

        if (kIsWeb && file.bytes == null) {
          print("Pemilihan file di Web gagal, bytes tidak ada.");
          return;
        }
        // Di Native, 'path' harus ada.
        if (!kIsWeb && file.path == null) {
          print("Pemilihan file di Native gagal, path tidak ada.");
          return;
        }

        context.read<ChatBloc>().add(GenerateBrandKitEvent(file));
      } else {
        print("Pemilihan gambar dibatalkan.");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error selecting image")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.select((ChatBloc bloc) => bloc.state is ChatLoading);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.3),
            spreadRadius: 2,
            blurRadius: 5,
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.attach_file, color: Colors.grey),
            onPressed: isLoading ? null : _pickAndAnalyzeFile,
          ),
          IconButton(
            icon: const Icon(Icons.camera_alt, color: Colors.grey),
            tooltip: "Generate brand ideas from product image", // Tambah tooltip
            onPressed: isLoading ? null : _pickAndGenerateBrandKit, // Panggil fungsi gambar
          ),
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration.collapsed(
                hintText: 'Ask Orchestrator...',
              ),
              onSubmitted: isLoading ? null : (_) => _sendMessage(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Colors.blueAccent),
            onPressed: isLoading ? null : _sendMessage,
          ),
        ],
      ),
    );
  }
}