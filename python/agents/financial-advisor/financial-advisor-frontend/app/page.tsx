"use client";

import { useState, useRef, useEffect } from "react";
import { Bot, Send, TrendingUp, User } from "lucide-react";

// Use environment variable or fallback to localhost for development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Message {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI Financial Advisor. I can help you with investment strategies, market analysis, risk assessment, and financial planning. What would you like to discuss today?",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatText = (text: string) => {
    // Convert various markdown-like formatting to JSX
    let formatted = text;
    
    // Handle line breaks
    const lines = formatted.split('\n');
    const elements: React.ReactNode[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.trim() === '') {
        elements.push(<br key={i} />);
        continue;
      }
      
      // Check for headers (lines with === or similar)
      if (line.includes('===') || line.includes('---')) {
        const headerText = line.replace(/[=\-]/g, '').trim();
        if (headerText) {
          elements.push(
            <h3 key={i} className="text-lg font-semibold text-blue-600 dark:text-blue-400 my-2">
              {headerText}
            </h3>
          );
        }
        continue;
      }
      
      // Handle bullet points
      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        elements.push(
          <div key={i} className="flex items-start ml-4 my-1">
            <span className="text-blue-500 mr-2">•</span>
            <span>{line.trim().substring(1).trim()}</span>
          </div>
        );
        continue;
      }
      
      // Handle bold text with <strong> tags
      if (line.includes('<strong>') && line.includes('</strong>')) {
        const parts = line.split(/(<strong>.*?<\/strong>)/);
        elements.push(
          <div key={i} className="my-1">
            {parts.map((part, partIndex) => {
              if (part.startsWith('<strong>') && part.endsWith('</strong>')) {
                return (
                  <strong key={partIndex} className="font-semibold text-slate-800 dark:text-slate-200">
                    {part.replace(/<\/?strong>/g, '')}
                  </strong>
                );
              }
              return part;
            })}
          </div>
        );
        continue;
      }
      
      // Regular line
      elements.push(
        <div key={i} className="my-1">
          {line}
        </div>
      );
    }
    
    return <div className="space-y-1">{elements}</div>;
  };

  const handleStreamingSubmit = async (userMessage: string) => {
    setIsLoading(true);
    
    // Add user message
    const newUserMessage: Message = { role: "user", content: userMessage };
    setMessages(prev => [...prev, newUserMessage]);
    
    // Add streaming assistant message
    const streamingMessage: Message = { role: "assistant", content: "", streaming: true };
    setMessages(prev => [...prev, streamingMessage]);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, streaming: true }),
      });
      
      if (!response.body) {
        throw new Error("No response body");
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                accumulatedText += data.token;
                setMessages(prev => prev.map((msg, index) => 
                  index === prev.length - 1 && msg.streaming
                    ? { ...msg, content: accumulatedText }
                    : msg
                ));
              } else if (data.done) {
                setMessages(prev => prev.map((msg, index) => 
                  index === prev.length - 1 && msg.streaming
                    ? { ...msg, streaming: false }
                    : msg
                ));
              } else if (data.error) {
                throw new Error(data.error);
              }
            } catch (e) {
              // Ignore JSON parse errors for malformed chunks
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      // Fallback to non-streaming
      setMessages(prev => prev.slice(0, -1)); // Remove the streaming message
      await handleNonStreamingSubmit(userMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNonStreamingSubmit = async (userMessage: string) => {
    setIsLoading(true);
    
    const newUserMessage: Message = { role: "user", content: userMessage };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, streaming: false }),
      });

      if (response.ok) {
        const data = await response.json();
        const botMessage: Message = { role: "assistant", content: data.reply };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    
    if (streamingEnabled) {
      await handleStreamingSubmit(userMessage);
    } else {
      await handleNonStreamingSubmit(userMessage);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-slate-900/60">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Financial Advisor
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                AI-powered investment guidance
              </p>
            </div>
          </div>
          
          {/* Streaming Toggle */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-slate-600 dark:text-slate-400">
              Streaming:
            </label>
            <button
              onClick={() => setStreamingEnabled(!streamingEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                streamingEnabled 
                  ? 'bg-blue-500' 
                  : 'bg-slate-300 dark:bg-slate-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  streamingEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start space-x-4 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg">
                  <Bot className="h-5 w-5" />
                </div>
              )}
              
              <div
                className={`group relative max-w-[75%] rounded-2xl px-4 py-3 shadow-lg ${
                  message.role === "user"
                    ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
                    : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                }`}
              >
                <div
                  className={`text-sm leading-relaxed ${
                    message.role === "user"
                      ? "text-white"
                      : "text-slate-700 dark:text-slate-300"
                  }`}
                >
                  {message.role === "assistant" ? formatText(message.content) : message.content}
                  {message.streaming && (
                    <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
                  )}
                </div>
              </div>
              
              {message.role === "user" && (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white shadow-lg">
                  <User className="h-5 w-5" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-slate-900/60">
        <div className="mx-auto max-w-4xl p-6">
          <form onSubmit={handleSubmit} className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about investments, stocks, portfolio management, or financial planning..."
                className="w-full resize-none rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-500 dark:placeholder:text-slate-400 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50 min-h-[50px] max-h-[150px] shadow-lg"
                rows={1}
                disabled={isLoading}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            </div>
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg transition-all hover:from-blue-600 hover:to-purple-700 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:shadow-lg"
            >
              {isLoading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
