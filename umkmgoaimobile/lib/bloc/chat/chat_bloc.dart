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
      String finalAnswer = "";

      // 3. Format the AI response based on the agent used
      if (agentUsed == "LEGAL") {
        finalAnswer = response['answer'] ?? "No answer found.";
        final List<dynamic> chunks = response['retrieved_chunks'] ?? [];
        if (chunks.isNotEmpty) {
          finalAnswer += "\n\n--- Sumber Dokumen ---";
          for (var chunk in chunks.take(2)) { // Show top 2 sources
            finalAnswer += "\n- ${chunk['chunk_id']} (${chunk['chapter_title']})";
          }
        }
      } else if (agentUsed == "MARKETING") {
        finalAnswer = response['answer'] ?? "No answer found.";
        // Optionally add logic to show article sources here
      } else { // UNKNOWN
        finalAnswer = response['answer'] ?? "Maaf, terjadi kesalahan.";
      }

      final aiMessage = ChatMessage(text: finalAnswer, isUser: false);

      // 4. Emit Loaded state with the updated message list
      emit(ChatLoaded(messages: List<ChatMessage>.from(currentStateMessages)..add(aiMessage)));

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