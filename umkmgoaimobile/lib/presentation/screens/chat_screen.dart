// File: mobile_app/lib/presentation/screens/chat_screen.dart

import 'package:flutter/material.dart';
import '../../data/services/api_service.dart';
import 'package:file_picker/file_picker.dart';

// A simple class to hold message data
class ChatMessage {
  final String text;
  final bool isUser;

  ChatMessage({required this.text, required this.isUser});
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final ApiService _apiService = ApiService();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  // --- Core Logic ---
  Future<void> _sendMessage() async {
    final String query = _textController.text;
    if (query.isEmpty) return;

    // Add user message to the list
    setState(() {
      _messages.add(ChatMessage(text: query, isUser: true));
      _isLoading = true;
    });
    _textController.clear();

    try {
      // Selalu panggil orkestrator untuk query teks
      final response = await _apiService.askOrchestrator(query);

      final String agentUsed = response['agent_used'] ?? 'UNKNOWN';
      String finalAnswer = "";

      // Logika untuk memformat jawaban berdasarkan agen yang digunakan
      if (agentUsed == "LEGAL") {
        finalAnswer = response['answer'] ?? "No answer found.";
        final List<dynamic> chunks = response['retrieved_chunks'] ?? [];
        if (chunks.isNotEmpty) {
          finalAnswer += "\\n\\n--- Sumber Dokumen ---";
          for (var chunk in chunks.take(2)) { // Tampilkan 2 sumber teratas
            finalAnswer += "\\n- ${chunk['chunk_id']} (${chunk['chapter_title']})";
          }
        }
      } else if (agentUsed == "MARKETING") {
        finalAnswer = response['answer'] ?? "No answer found.";
        // Di sini kita bisa menambahkan logika untuk menampilkan sumber artikel jika perlu
      } else { // UNKNOWN
        finalAnswer = response['answer'] ?? "Maaf, terjadi kesalahan.";
      }

      setState(() {
        _messages.add(ChatMessage(text: finalAnswer, isUser: false));
      });

    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: "Error: ${e.toString()}", isUser: false));
      });
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  Future<void> _pickAndAnalyzeFile() async {
    setState(() { _isLoading = true; });

    try {
      // Buka dialog pemilih file, batasi hanya untuk CSV
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
      );

      if (result != null && result.files.single.bytes != null) {
        final file = result.files.single;

        // Beri feedback langsung ke UI
        setState(() {
          _messages.add(ChatMessage(text: "Menganalisis file: ${file.name}...", isUser: true));
        });

        // Panggil ApiService
        final response = await _apiService.analyzeSalesData(file);

        final String insights = response['insights'] ?? "No insights found.";
        // Kita bisa format statistik untuk ditampilkan juga
        final Map<String, dynamic> stats = response['statistics'] ?? {};
        final String formattedStats =
            "Total Pendapatan: ${stats['total_revenue']?.toStringAsFixed(0) ?? 'N/A'}\\n"
            "Produk Terlaris (Jumlah): ${stats['best_selling_by_quantity']?['name'] ?? 'N/A'}\\n"
            "Produk Pendapatan Tertinggi: ${stats['highest_revenue_product']?['name'] ?? 'N/A'}";

        final String finalAnswer = "$insights\\n\\n--- Ringkasan Statistik ---\\n$formattedStats";

        setState(() {
          _messages.add(ChatMessage(text: finalAnswer, isUser: false));
        });

      } else {
        // Pengguna membatalkan pemilihan file
        print("File picking cancelled.");
      }
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: "Error saat menganalisis file: ${e.toString()}", isUser: false));
      });
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  // --- UI Building ---
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('UMKM-Go AI'),
        backgroundColor: Colors.blueAccent,
      ),
      body: Column(
        children: [
          // Chat messages area
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildChatBubble(message);
              },
            ),
          ),
          // Loading indicator
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          // Input area
          _buildInputArea(),
        ],
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

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            spreadRadius: 2,
            blurRadius: 5,
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.attach_file, color: Colors.grey),
            onPressed: _isLoading ? null : _pickAndAnalyzeFile,
          ),
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration.collapsed(
                hintText: 'Tanyakan sesuatu...',
              ),
              onSubmitted: (value) => _sendMessage(),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send, color: Colors.blueAccent),
            onPressed: _isLoading ? null : _sendMessage,
          ),
        ],
      ),
    );
  }
}