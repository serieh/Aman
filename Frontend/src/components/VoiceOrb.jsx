import React, { useEffect, useRef } from 'react';

function addAlphaToHex(hex, alpha) {
  if (!hex || !hex.startsWith('#')) return hex;
  const cleanHex = hex.slice(0, 7);
  const alphaHex = Math.round(alpha * 255).toString(16).padStart(2, '0');
  return cleanHex + alphaHex;
}

export default function VoiceOrb({ state, micAnalyser, playAnalyser, isRecording }) {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const bufferLength = 128;
    const dataArray = new Uint8Array(bufferLength);

    const drawBlob = (cContext, cx, cy, radius, noiseAmp, timeOffset, color, opacity) => {
      cContext.save();
      cContext.globalAlpha = opacity;
      cContext.beginPath();
      
      const points = [];
      const steps = 14; // control points for organic liquid shape
      for (let i = 0; i < steps; i++) {
        const angle = (i / steps) * Math.PI * 2;
        const wave1 = Math.sin(angle * 3 + timeOffset) * noiseAmp;
        const wave2 = Math.cos(angle * 2 - timeOffset * 1.3) * (noiseAmp * 0.45);
        const wave3 = Math.sin(angle * 5 + timeOffset * 2.1) * (noiseAmp * 0.2);
        const r = radius + wave1 + wave2 + wave3;
        
        points.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r
        });
      }
      
      // Smooth closed curve using quadratic curves through midpoints
      cContext.moveTo(points[0].x, points[0].y);
      for (let i = 0; i < points.length; i++) {
        const currentPoint = points[i];
        const nextPoint = points[(i + 1) % points.length];
        const ctrlX = (currentPoint.x + nextPoint.x) / 2;
        const ctrlY = (currentPoint.y + nextPoint.y) / 2;
        cContext.quadraticCurveTo(currentPoint.x, currentPoint.y, ctrlX, ctrlY);
      }
      
      cContext.closePath();
      
      const grad = cContext.createRadialGradient(
        cx, 
        cy, 
        radius * 0.1, 
        cx, 
        cy, 
        radius * 1.5
      );
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.3, color);
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      
      cContext.fillStyle = grad;
      cContext.fill();
      cContext.restore();
    };

    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const cssWidth = rect.width || canvas.offsetWidth || 300;
      const cssHeight = rect.height || canvas.offsetHeight || 300;

      const dpr = window.devicePixelRatio || 1;
      const targetWidth = Math.floor(cssWidth * dpr);
      const targetHeight = Math.floor(cssHeight * dpr);

      if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
        canvas.width = targetWidth;
        canvas.height = targetHeight;
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, cssWidth, cssHeight);

      const centerX = cssWidth / 2;
      const centerY = cssHeight / 2;
      
      let audioVolume = 0;
      let activeAnalyser = null;

      if (state === 'listening' && micAnalyser) {
        activeAnalyser = micAnalyser;
      } else if (state === 'speaking' && playAnalyser) {
        activeAnalyser = playAnalyser;
      }

      if (activeAnalyser) {
        try {
          activeAnalyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          audioVolume = sum / bufferLength / 255;
        } catch (e) {
          console.error("Audio analyser failed:", e);
        }
      }

      const targetIntensity = audioVolume * 1.5;
      phaseRef.current += 1.5 + targetIntensity * 5;

      // Extract current theme colors dynamically
      let themePrimary = '#6366f1'; // Indigo fallback
      let themeSecondary = '#a855f7'; // Purple fallback
      let themeTertiary = '#8b5cf6'; // Violet fallback
      
      try {
        const bodyStyle = getComputedStyle(document.body);
        const p = bodyStyle.getPropertyValue('--color-primary').trim();
        const s = bodyStyle.getPropertyValue('--color-secondary').trim();
        const t = bodyStyle.getPropertyValue('--color-tertiary').trim();
        if (p) themePrimary = p;
        if (s) themeSecondary = s;
        if (t) themeTertiary = t;
      } catch (e) {
        console.error("Failed to read theme colors:", e);
      }

      let baseRadius = 75;
      let glowColor1 = themePrimary;
      let glowColor2 = themeSecondary;
      let ringColor = addAlphaToHex(themePrimary, 0.15);
      let pulseSpeed = 0.02;
      let noiseAmplitude = 8;

      if (state === 'listening') {
        baseRadius = 80;
        glowColor1 = themeSecondary;
        glowColor2 = themeTertiary;
        noiseAmplitude = 10 + targetIntensity * 32;
      } else if (state === 'speaking') {
        baseRadius = 85;
        glowColor1 = themePrimary;
        glowColor2 = themeSecondary;
        noiseAmplitude = 12 + targetIntensity * 42;
      } else if (state === 'thinking') {
        baseRadius = 70 + Math.sin(phaseRef.current * 0.05) * 5;
        glowColor1 = themeTertiary;
        glowColor2 = themePrimary;
        noiseAmplitude = 4;
      } else if (state === 'transcribing') {
        baseRadius = 72;
        glowColor1 = themeSecondary;
        glowColor2 = themeTertiary;
        noiseAmplitude = 5;
      } else if (state === 'muted') {
        baseRadius = 70;
        glowColor1 = 'rgba(148, 163, 184, 0.7)'; // Slate Gray
        glowColor2 = 'rgba(100, 116, 139, 0.4)';
        noiseAmplitude = 1.5;
        pulseSpeed = 0.005;
      } else { // Idle
        baseRadius = 75 + Math.sin(phaseRef.current * pulseSpeed) * 3;
        glowColor1 = themePrimary;
        glowColor2 = themeSecondary;
        noiseAmplitude = 3.5;
      }



      // Layered fluid rendering for high-fidelity liquid orb aesthetic
      const timeOffset = phaseRef.current * 0.012;
      
      // Layer 1: Faint outer atmospheric blob
      drawBlob(ctx, centerX, centerY, baseRadius * 1.25, noiseAmplitude * 1.35, timeOffset, glowColor2, 0.22);
      
      // Layer 2: Rich middle liquid blob (opposite rotation)
      drawBlob(ctx, centerX, centerY, baseRadius * 1.0, noiseAmplitude * 0.9, -timeOffset * 1.4, glowColor1, 0.48);

      // Layer 3: Opaque white hot core
      drawBlob(ctx, centerX, centerY, baseRadius * 0.78, noiseAmplitude * 0.4, timeOffset * 2.1, '#ffffff', 0.88);

      ctx.restore();

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [state, micAnalyser, playAnalyser]);

  return (
    <div className="relative w-72 h-72 md:w-80 md:h-80 mx-auto select-none pointer-events-none">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ display: 'block' }}
      />
    </div>
  );
}
