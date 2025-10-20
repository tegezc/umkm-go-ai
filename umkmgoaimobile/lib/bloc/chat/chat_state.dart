// File: mobile_app/lib/bloc/chat/chat_state.dart
part of 'chat_bloc.dart';

// Simple class to hold message data (same as before)
class ChatMessage extends Equatable {
  final String text;
  final bool isUser;

  const ChatMessage({required this.text, required this.isUser});

  @override
  List<Object?> get props => [text, isUser];
}

abstract class ChatState extends Equatable {
  final List<ChatMessage> messages;

  const ChatState({required this.messages});

  @override
  List<Object?> get props => [messages];
}

// Initial state, before any interaction
class ChatInitial extends ChatState {
  const ChatInitial() : super(messages: const []);
}

// State when the BLoC is processing a request (show loading indicator)
class ChatLoading extends ChatState {
  const ChatLoading({required List<ChatMessage> messages}) : super(messages: messages);
}

// State when the BLoC has successfully received a response (update message list)
class ChatLoaded extends ChatState {
  const ChatLoaded({required List<ChatMessage> messages}) : super(messages: messages);
}

// State when an error occurred
class ChatError extends ChatState {
  final String error;

  const ChatError({required List<ChatMessage> messages, required this.error})
      : super(messages: messages);

  @override
  List<Object?> get props => [messages, error];
}