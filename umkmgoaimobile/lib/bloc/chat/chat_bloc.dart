// File: mobile_app/lib/bloc/chat/chat_bloc.dart

import 'package:equatable/equatable.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/services/api_service.dart';

part 'chat_event.dart';
part 'chat_state.dart';

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ApiService apiService; // Inject ApiService

  ChatBloc({required this.apiService}) : super(const ChatInitial()) {
    // Register handlers for each event
    on<SendTextMessageEvent>(_onSendTextMessage);
    on<AnalyzeFileEvent>(_onAnalyzeFile);
  }

  // --- Event Handler for Text Messages ---
  Future<void> _onSendTextMessage(
      SendTextMessageEvent event,
      Emitter<ChatState> emit,
      ) async {
    // 1. Add user message and emit Loading state
    final userMessage = ChatMessage(text: event.query, isUser: true);
    final currentStateMessages = List<ChatMessage>.from(state.messages)..add(userMessage);
    emit(ChatLoading(messages: currentStateMessages));

    try {
      // 2. Call ApiService (Orchestrator)
      final response = await apiService.askOrchestrator(event.query);
      final String agentUsed = response['agent_used'] ?? 'UNKNOWN';

      List<ChatMessage> aiMessages = []; // Tampung pesan AI di sini

      if (agentUsed == "LEGAL" || agentUsed == "MARKETING") {
        String answer = response['answer'] ?? "No answer found.";
        // Tambahkan sumber jika ada (contoh untuk Legal)
        if (agentUsed == "LEGAL") {
          final List<dynamic> chunks = response['retrieved_chunks'] ?? [];
          if (chunks.isNotEmpty) {
            answer += "\n\n--- Sumber Dokumen ---";
            for (var chunk in chunks.take(2)) {
              answer += "\n- ${chunk['chunk_id']} (${chunk['chapter_title']})";
            }
          }
        }else if (agentUsed == "MARKETING") {
          answer = response['answer'] ?? "No answer found.";
          // Optionally add logic to show article sources here
        }else { // UNKNOWN
          answer = response['answer'] ?? "Maaf, terjadi kesalahan.";
        }
        aiMessages.add(ChatMessage(text: answer, isUser: false));

      } else if (agentUsed == "BRAND_AGENT") { // Asumsi backend mengembalikan 'BRAND_AGENT'
        final brandKit = response['brand_kit'];
        if (brandKit != null) {
          // Pesan teks utama (nama, tagline, bio)
          String brandText = "Berikut hasil analisis dan ide mereknya:\n\n"
              "Nama: ${brandKit['suggested_names']?.join(', ')}\n"
              "Tagline: ${brandKit['suggested_taglines']?.join(', ')}\n"
              "Bio IG: ${brandKit['instagram_bio']}";
          aiMessages.add(ChatMessage(text: brandText, isUser: false));

          // Pesan terpisah untuk setiap konsep logo
          final List<dynamic> logoConcepts = brandKit['logo_concepts'] ?? [];
          for (var concept in logoConcepts) {
            aiMessages.add(ChatMessage(
              text: "Konsep Logo: ${concept['description']}",
              imageUrl: concept['image_url'], // Sertakan URL gambar
              isUser: false,
            ));
          }
        } else {
          aiMessages.add(const ChatMessage(text: "Gagal memproses brand kit.", isUser: false));
        }
      } else { // UNKNOWN atau error lainnya
        final answer = response['answer'] ?? "Maaf, terjadi kesalahan.";
        aiMessages.add(ChatMessage(text: answer, isUser: false));
      }

      // Emit Loaded state dengan semua pesan AI yang baru
      emit(ChatLoaded(messages: List<ChatMessage>.from(currentStateMessages)..addAll(aiMessages)));

    } catch (e) {
      // 5. Emit Error state if something went wrong
      final errorMessage = ChatMessage(text: "Error: ${e.toString()}", isUser: false);
      emit(ChatError(messages: List<ChatMessage>.from(currentStateMessages)..add(errorMessage), error: e.toString()));
    }
  }

  // --- Event Handler for File Analysis ---
  Future<void> _onAnalyzeFile(
      AnalyzeFileEvent event,
      Emitter<ChatState> emit,
      ) async {
    // 1. Add feedback message and emit Loading state
    final feedbackMessage = ChatMessage(text: "Menganalisis file: ${event.file.name}...", isUser: true);
    final currentStateMessages = List<ChatMessage>.from(state.messages)..add(feedbackMessage);
    emit(ChatLoading(messages: currentStateMessages));

    try {
      // 2. Call ApiService
      final response = await apiService.analyzeSalesData(event.file);
      final String insights = response['insights'] ?? "No insights found.";
      final Map<String, dynamic> stats = response['statistics'] ?? {};
      final String formattedStats =
          "Total Pendapatan: ${stats['total_revenue']?.toStringAsFixed(0) ?? 'N/A'}\n"
          "Produk Terlaris (Jumlah): ${stats['best_selling_by_quantity']?['name'] ?? 'N/A'}\n"
          "Produk Pendapatan Tertinggi: ${stats['highest_revenue_product']?['name'] ?? 'N/A'}";

      final String finalAnswer = "$insights\n\n--- Ringkasan Statistik ---\n$formattedStats";
      final aiMessage = ChatMessage(text: finalAnswer, isUser: false);

      // 3. Emit Loaded state
      emit(ChatLoaded(messages: List<ChatMessage>.from(currentStateMessages)..add(aiMessage)));

    } catch (e) {
      // 4. Emit Error state
      final errorMessage = ChatMessage(text: "Error saat menganalisis file: ${e.toString()}", isUser: false);
      emit(ChatError(messages: List<ChatMessage>.from(currentStateMessages)..add(errorMessage), error: e.toString()));
    }
  }
}