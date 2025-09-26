import React, { useRef, useState } from 'react';

interface ChatMessage {
  id: number;
  sender: 'user' | 'ai';
  text?: string;
  file?: File;
  fileUrl?: string;
  fileType?: string;
}

function App(): React.JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (!input.trim()) return;
    const newMsg: ChatMessage = {
      id: Date.now(),
      sender: 'user',
      text: input,
    };
    setMessages((msgs) => [...msgs, newMsg]);
    setInput('');
    // Mock AI reply
    setTimeout(() => {
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now() + 1,
          sender: 'ai',
          text: 'This is a mock AI response.',
        },
      ]);
    }, 800);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, type: 'image' | 'file') => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fileUrl = URL.createObjectURL(file);
    setMessages((msgs) => [
      ...msgs,
      {
        id: Date.now(),
        sender: 'user',
        file,
        fileUrl,
        fileType: type,
      },
    ]);
    // Mock AI reply
    setTimeout(() => {
      setMessages((msgs) => [
        ...msgs,
        {
          id: Date.now() + 1,
          sender: 'ai',
          text: 'AI received your ' + (type === 'image' ? 'image.' : 'document.'),
        },
      ]);
    }, 800);
    // Reset input value so same file can be uploaded again
    e.target.value = '';
  };

  return (
    <div className="chat-app">
      <div className="chat-main">
        <div className="chat-area">
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.sender}`}>
                {msg.text && <div className="chat-bubble">{msg.text}</div>}
                {msg.file && msg.fileType === 'image' && msg.fileUrl && (
                  <img src={msg.fileUrl} alt="uploaded" className="chat-image" />
                )}
                {msg.file && msg.fileType === 'file' && msg.fileUrl && (
                  <a href={msg.fileUrl} download={msg.file.name} className="chat-file">
                    {msg.file.name}
                  </a>
                )}
              </div>
            ))}
          </div>
          <div className="chat-input-bar">
            <div className="chat-input-row">
              <button
                className="upload-btn"
                title="Upload Image"
                onClick={() => imageInputRef.current?.click()}
              >
                🖼️
              </button>
              <input
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                ref={imageInputRef}
                onChange={(e) => handleFileUpload(e, 'image')}
              />
              <button
                className="upload-btn"
                title="Upload Document"
                onClick={() => fileInputRef.current?.click()}
              >
                📄
              </button>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt,.ppt,.pptx,.xls,.xlsx,.csv,application/*"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={(e) => handleFileUpload(e, 'file')}
              />
              <input
                className="chat-input"
                type="text"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button className="send-btn" onClick={handleSend}>
                ➤
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
