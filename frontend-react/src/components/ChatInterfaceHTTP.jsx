// ChatInterfaceHTTP.jsx
// HTTP version (no WebSocket) - easier to integrate if WebSocket is blocked

import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';

const ChatInterfaceHTTP = ({ userId = 'user123', onComplete }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 5 });
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Start chat session on mount
  useEffect(() => {
    startChat();
  }, []);

  const startChat = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`http://localhost:8001/chat/start?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to start chat');
      }
      
      const data = await response.json();
      
      setSessionId(data.session_id);
      setProgress(data.progress);
      
      // Add greeting message
      setMessages([{
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toLocaleTimeString()
      }]);
      
      setError(null);
    } catch (err) {
      console.error('Error starting chat:', err);
      setError('Failed to connect to chat service');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (text) => {
    if (!text.trim() || !sessionId || isLoading) return;
    
    // Add user message to UI
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input
    setInputValue('');
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8001/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: text
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const data = await response.json();
      
      // Add AI response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message,
        options: data.options,
        timestamp: new Date().toLocaleTimeString()
      }]);
      
      // Update progress
      if (data.progress) {
        setProgress(data.progress);
      }
      
      // Check if complete
      if (data.complete && data.summary) {
        // Get final intent
        await completeChat();
      }
      
      setError(null);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message');
      
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const completeChat = async () => {
    try {
      const response = await fetch(`http://localhost:8001/chat/complete?session_id=${sessionId}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to complete chat');
      }
      
      const data = await response.json();
      
      console.log('Chat completed:', data);
      
      // Pass intent to parent component
      if (onComplete) {
        onComplete(data.intent, data.context);
      }
    } catch (err) {
      console.error('Error completing chat:', err);
    }
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

  const handleRetry = () => {
    setError(null);
    startChat();
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-avatar">🤖</div>
          <div className="chat-header-info">
            <h3>AI DevOps Assistant</h3>
            <span className={`status ${sessionId ? 'online' : 'offline'}`}>
              {sessionId ? '● Online' : '○ Offline'}
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

      {/* Error Banner */}
      {error && (
        <div className="chat-error-banner">
          <span>⚠️ {error}</span>
          <button onClick={handleRetry}>Retry</button>
        </div>
      )}

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && !isLoading && (
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
                      disabled={isLoading}
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
        {isLoading && (
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
          disabled={!sessionId || isLoading}
        />
        <button 
          type="submit" 
          className="chat-send-btn"
          disabled={!inputValue.trim() || !sessionId || isLoading}
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

export default ChatInterfaceHTTP;
