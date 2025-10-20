// File: mobile_app/lib/presentation/screens/chat_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:file_picker/file_picker.dart';
import '../../data/services/api_service.dart';
import '../../bloc/chat/chat_bloc.dart';

class ChatScreen extends StatelessWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // 1. Sediakan BLoC ke Widget Tree menggunakan BlocProvider
    return BlocProvider(
      // Buat instance ChatBloc, inject ApiService
      create: (context) => ChatBloc(apiService: ApiService()),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('UMKM-Go AI'),
          backgroundColor: Colors.blueAccent,
        ),
        body: Column(
          children: [
            // 2. Gunakan BlocBuilder untuk membangun daftar pesan
            Expanded(
              child: BlocBuilder<ChatBloc, ChatState>(
                builder: (context, state) {
                  // Tampilkan pesan error jika state adalah ChatError
                  if (state is ChatError && state.messages.isEmpty) {
                    return Center(child: Text('Error: ${state.error}'));
                  }
                  // Tampilkan pesan "mulai percakapan" jika initial
                  if (state.messages.isEmpty) {
                    return const Center(child: Text('Mulai percakapan...'));
                  }
                  // Bangun ListView berdasarkan messages dari state saat ini
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
            // 3. Gunakan BlocSelector untuk menampilkan loading indicator
            BlocSelector<ChatBloc, ChatState, bool>(
              selector: (state) => state is ChatLoading, // Hanya rebuild jika loading berubah
              builder: (context, isLoading) {
                return isLoading
                    ? const Padding(
                  padding: EdgeInsets.all(8.0),
                  child: CircularProgressIndicator(),
                )
                    : const SizedBox.shrink();
              },
            ),
            // 4. Input area (UI tetap sama, logic berubah)
            const _InputArea(),
          ],
        ),
      ),
    );
  }

  Widget _buildChatBubble(ChatMessage message) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 5.0, horizontal: 8.0),
        padding: const EdgeInsets.all(12.0),
        decoration: BoxDecoration(
          color: message.isUser ? Colors.blue[300] : Colors.grey[200],
          borderRadius: BorderRadius.circular(15.0),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: message.isUser ? Colors.white : Colors.black87,
          ),
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
      );

      if (result != null && result.files.single.bytes != null) {
        context.read<ChatBloc>().add(AnalyzeFileEvent(result.files.single));
      } else {
        print("Pemilihan file dibatalkan.");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error memilih file: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // Dengarkan state loading untuk menonaktifkan tombol
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
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration.collapsed(
                hintText: 'Tanya Orkestrator...',
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