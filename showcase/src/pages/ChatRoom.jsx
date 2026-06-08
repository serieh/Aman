import React, { useEffect } from 'react';
import { useParams, Navigate, useNavigate, useSearchParams } from 'react-router-dom';

import Slide1_Intro from '../components/slides/Slide1_Intro';
import Slide2_Features from '../components/slides/Slide2_Features';
import Slide3_Latency from '../components/slides/Slide3_Latency';
import Slide4_ScriptedChat from '../components/slides/Slide4_ScriptedChat';
import Slide5_Conclusion from '../components/slides/Slide5_Conclusion';
import Slide6_Closing from '../components/slides/Slide6_Closing';

export default function ChatRoom() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isAutoPlay = searchParams.get('autoPlay') === 'true';

  useEffect(() => {
    if (!isAutoPlay) return;

    if (['1', '2', '3', '5'].includes(chatId)) {
      const timer = setTimeout(() => {
        navigate(`/app/chat/${parseInt(chatId) + 1}?autoPlay=true`);
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [chatId, isAutoPlay, navigate]);

  const handleDemoComplete = () => {
    if (isAutoPlay) {
      setTimeout(() => {
         navigate(`/app/chat/5?autoPlay=true`);
      }, 3000); // Wait 3s after demo finishes before advancing
    }
  };

  const renderSlide = () => {
    switch (chatId) {
      case '1': return <Slide1_Intro />;
      case '2': return <Slide2_Features />;
      case '3': return <Slide3_Latency />;
      case '4': return <Slide4_ScriptedChat isAutoPlay={isAutoPlay} onAutoComplete={handleDemoComplete} />;
      case '5': return <Slide5_Conclusion />;
      case '6': return <Slide6_Closing />;
      default: return <Navigate to="/app/chat/1" replace />;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full aman-gradient-bg overflow-hidden relative">
      {renderSlide()}
    </div>
  );
}
