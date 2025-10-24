// File: mobile_app/lib/bloc/chat/chat_bloc.dart

import 'package:equatable/equatable.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/services/api_service.dart';

part 'chat_event.dart';
part 'chat_state.dart';

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ApiService apiService;

  ChatBloc({required this.apiService}) : super(const ChatInitial()) {
    // Register handlers for each event
    on<SendTextMessageEvent>(_onSendTextMessage);
    on<AnalyzeFileEvent>(_onAnalyzeFile);
    on<GenerateBrandKitEvent>(_onGenerateBrandKit);
  }

  // --- Event Handler for Text Messages ---
  Future<void> _onSendTextMessage(
      SendTextMessageEvent event,
      Emitter<ChatState> emit,
      ) async {
    // 1. Add user message and emit Loading state
    final userMessage = ChatMessage(text: event.query, type: MessageType.user);
    var currentMessages = List<ChatMessage>.from(state.messages)..add(userMessage);

    final loadingMessage = ChatMessage(text: "Processing...", type: MessageType.loading);
    currentMessages.add(loadingMessage);
    emit(ChatLoading(messages: currentMessages));

    try {
      // 2. Call ApiService (Orchestrator)
      final response = await apiService.askOrchestrator(event.query);
      final String agentUsed = response['agent_used'] ?? 'UNKNOWN';

      List<ChatMessage> aiMessages = [];

      if (agentUsed == "LEGAL" || agentUsed == "MARKETING") {
        String answer = response['answer'] ?? "No answer found.";
        if (agentUsed == "LEGAL") {
          final List<dynamic> chunks = response['retrieved_chunks'] ?? [];
          if (chunks.isNotEmpty) {
            answer += "\n\n--- Document Source ---";
            for (var chunk in chunks.take(2)) {
              answer += "\n- ${chunk['chunk_id']} (${chunk['chapter_title']})";
            }
          }
        }else if (agentUsed == "MARKETING") {
          answer = response['answer'] ?? "No answer found.";
        }else { // UNKNOWN
          answer = response['answer'] ?? "Sorry — something went wrong.";
        }
        aiMessages.add(ChatMessage(text: answer, type: MessageType.ai));

      } else if (agentUsed == "BRAND_AGENT") {
        final brandKit = response['brand_kit'];
        if (brandKit != null) {
          String brandText = "Here are the analysis results...\n...";
          aiMessages.add(ChatMessage(text: brandText, type: MessageType.ai));
          final List<dynamic> logoConcepts = brandKit['logo_concepts'] ?? [];
          for (var concept in logoConcepts) {
            aiMessages.add(ChatMessage(
              text: "Logo Concept:: ${concept['description']}",
              imageUrl: concept['image_url'],
              type: MessageType.ai,
            ));
          }
        } else {
          aiMessages.add(const ChatMessage(text: "Failed to process brand kit.",type: MessageType.ai));
        }
      } else {
        final answer = response['answer'] ?? "Sorry — something went wrong.";
        aiMessages.add(ChatMessage(text: answer, type: MessageType.ai));
      }

      currentMessages.removeLast();
      currentMessages.addAll(aiMessages);
      emit(ChatLoaded(messages: currentMessages));

    } catch (e) {
      // 5. Emit Error state if something went wrong
      final errorMessage = ChatMessage(text: "Error: ${e.toString()}", type: MessageType.error);
      emit(ChatError(messages: List<ChatMessage>.from(currentMessages)..add(errorMessage), error: e.toString()));
    }
  }

  // --- Event Handler for File Analysis ---
  Future<void> _onAnalyzeFile(
      AnalyzeFileEvent event,
      Emitter<ChatState> emit,
      ) async {
    // 1. Add feedback message and emit Loading state
    final feedbackMessage = ChatMessage(text: "Analyzing file: ${event.file.name}...", type: MessageType.user);
    var currentMessages = List<ChatMessage>.from(state.messages)..add(feedbackMessage);
    final loadingMessage = ChatMessage(text: "Analyzing...", type: MessageType.loading);
    currentMessages.add(loadingMessage);
    emit(ChatLoading(messages: currentMessages));


    try {
      // 2. Call ApiService
      final response = await apiService.analyzeSalesData(event.file);
      final String insights = response['insights'] ?? "No insights found.";
      final Map<String, dynamic> stats = response['statistics'] ?? {};
      final String formattedStats =
          "Total Revenue: ${stats['total_revenue']?.toStringAsFixed(0) ?? 'N/A'}\n"
          "Best-Selling Product (by Quantity): ${stats['best_selling_by_quantity']?['name'] ?? 'N/A'}\n"
          "Highest Revenue Product: ${stats['highest_revenue_product']?['name'] ?? 'N/A'}";

      final String finalAnswer = "$insights\n\n--- Statistics Summary ---\n$formattedStats";
      final aiMessage = ChatMessage(text: finalAnswer, type: MessageType.ai);

      // 3. Emit Loaded state
      currentMessages.removeLast(); // Hapus loading
      currentMessages.add(aiMessage);
      emit(ChatLoaded(messages: currentMessages));

    } catch (e) {
      currentMessages.removeLast();
      final errorMessage = ChatMessage(text: "Failed to process file: ${e.toString()}", type: MessageType.error); // Tipe Error
      emit(ChatError(messages: List<ChatMessage>.from(currentMessages)..add(errorMessage), error: e.toString()));
    }
  }

  Future<void> _onGenerateBrandKit(
      GenerateBrandKitEvent event,
      Emitter<ChatState> emit,
      ) async {
    final feedbackMessage = ChatMessage(
        text: "Generating brand concept from image: ${event.imageFile.name}...",
        type: MessageType.user,imageUrl: event.imageFile.path); // Tipe User
    var currentMessages = List<ChatMessage>.from(state.messages)
      ..add(feedbackMessage);

    final loadingMessage = ChatMessage(
        text: "Creating brand concept...", type: MessageType.loading);
    currentMessages.add(loadingMessage);
    emit(ChatLoading(messages: currentMessages));

    try {
      final response =
      await apiService.generateBrandKit(event.imageFile, event.businessName);
      List<ChatMessage> aiMessages = [];

      final brandKit = response['brand_kit'];
      if (brandKit != null) {
        String brandText = "Here are the analysis results and brand ideas:\n\n"
            "Name: ${brandKit['suggested_names']?.join(', ')}\n"
            "Tagline: ${brandKit['suggested_taglines']?.join(', ')}\n"
            "Bio IG: ${brandKit['instagram_bio']}";
        aiMessages.add(ChatMessage(text: brandText, type: MessageType.ai));

        final List<dynamic> logoConcepts = brandKit['logo_concepts'] ?? [];
        for (var concept in logoConcepts) {
          aiMessages.add(ChatMessage(
            text: "Logo Concept: ${concept['description']}",
            imageUrl: concept['image_url'],
            type: MessageType.ai,
          ));
        }
      } else {
        aiMessages.add(const ChatMessage(
            text: "Failed to process brand kit from API response.", type: MessageType.error));
      }

      currentMessages.removeLast();
      currentMessages.addAll(aiMessages);
      emit(ChatLoaded(messages: currentMessages));

    } catch (e) {

      currentMessages.removeLast();
      final errorMessage = ChatMessage(
          text: "An error occurred while generating the brand kit: ${e.toString()}",
          type: MessageType.error);
      emit(ChatError(
          messages: List<ChatMessage>.from(currentMessages)..add(errorMessage),
          error: e.toString()));
    }
  }
}