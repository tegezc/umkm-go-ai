// File: mobile_app/lib/bloc/chat/chat_event.dart
part of 'chat_bloc.dart';

abstract class ChatEvent extends Equatable {
  const ChatEvent();

  @override
  List<Object?> get props => [];
}

// Event triggered when the user sends a text message
class SendTextMessageEvent extends ChatEvent {
  final String query;

  const SendTextMessageEvent(this.query);

  @override
  List<Object?> get props => [query];
}

// Event triggered when the user selects a file to analyze
class AnalyzeFileEvent extends ChatEvent {
  final PlatformFile file;

  const AnalyzeFileEvent(this.file);

  @override
  List<Object?> get props => [file];
}

// Event triggered when the user selects an image for brand generation
class GenerateBrandKitEvent extends ChatEvent {
  final PlatformFile imageFile;
  final String businessName; // Kita bisa tambahkan input nama bisnis nanti

  const GenerateBrandKitEvent(this.imageFile, {this.businessName = "Usaha Saya"});

  @override
  List<Object?> get props => [imageFile, businessName];
}