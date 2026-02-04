// ChatInterface.jsx
// Complete chat UI component with WebSocket support

import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';

const ChatInterface = ({ userId = 'user123', onComplete }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 5 });
  const [sessionId, setSessionId] = useState(null);
  
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection - only create once
  useEffect(() => {
    // Prevent multiple connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    const ws = new WebSocket(`ws://localhost:8001/ws/chat/${userId}`);
    
    ws.onopen = () => {
      console.log('Chat connected');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);
      
      if (data.type === 'message') {
        // Add AI message
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.content,
          options: data.options,
          timestamp: new Date().toLocaleTimeString()
        }]);
        
        setIsTyping(false);
        
        // Update progress
        if (data.progress) {
          setProgress(data.progress);
        }
        
        // Store session ID
        if (data.session_id) {
          setSessionId(data.session_id);
        }
      } 
      else if (data.type === 'complete') {
        // Chat completed - pass intent to parent
        console.log('Chat completed with intent:', data.intent);
        if (onComplete) {
          onComplete(data.intent, data.context);
        }
      }
      else if (data.type === 'error') {
        console.error('Chat error:', data.message);
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Error: ${data.message}`,
          timestamp: new Date().toLocaleTimeString()
        }]);
        setIsTyping(false);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      console.log('Chat disconnected');
      setIsConnected(false);
    };
    
    wsRef.current = ws;
    
    // Cleanup - only close on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        console.log('Closing WebSocket connection');
        ws.close();
      }
    };
  }, []); // Empty dependency array - only run once!

  const sendMessage = (text) => {
    if (!text.trim() || !wsRef.current || !isConnected) return;
    
    // Add user message to UI
    setMessages(prev => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString()
    }]);
    
    // Send to backend
    wsRef.current.send(JSON.stringify({ message: text }));
    
    // Clear input
    setInputValue('');
    
    // Show typing indicator
    setIsTyping(true);
  };

  const handleQuickReply = (option) => {
    sendMessage(option.label);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-avatar">🤖</div>
          <div className="chat-header-info">
            <h3>AI DevOps Assistant</h3>
            <span className={`status ${isConnected ? 'online' : 'offline'}`}>
              {isConnected ? '● Online' : '○ Offline'}
            </span>
          </div>
        </div>
        <div className="chat-progress">
          <span>Progress: {progress.current}/{progress.total}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <p>Start chatting to create your infrastructure</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? '🤖' : 
               msg.role === 'system' ? '⚙️' : '👤'}
            </div>
            <div className="message-content">
              <div className="message-text">
                {msg.content}
              </div>
              
              {/* Quick reply buttons */}
              {msg.options && msg.options.length > 0 && (
                <div className="quick-replies">
                  {msg.options.map((option, i) => (
                    <button
                      key={i}
                      className="quick-reply-btn"
                      onClick={() => handleQuickReply(option)}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              )}
              
              <div className="message-time">{msg.timestamp}</div>
            </div>
          </div>
        ))}
        
        {/* Typing indicator */}
        {isTyping && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Type your message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!isConnected}
        />
        <button 
          type="submit" 
          className="chat-send-btn"
          disabled={!inputValue.trim() || !isConnected}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;