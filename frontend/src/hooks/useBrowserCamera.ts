import { useEffect, useRef, useState } from 'react';

export function useBrowserCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [active, setActive] = useState(false);
  const [cameraError, setCameraError] = useState('');

  async function start() {
    setCameraError('');
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Brauzer kamerasi uchun localhost yoki HTTPS kerak.');
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
      return true;
    } catch (error) {
      const name = error instanceof DOMException ? error.name : '';
      setCameraError(
        name === 'NotAllowedError'
          ? 'Kamera ruxsati berilmadi. Brauzer sozlamalaridan kameraga ruxsat bering.'
          : name === 'NotFoundError'
            ? 'Kamera qurilmasi topilmadi.'
            : 'Kamera ochilmadi. Boshqa dastur kamerani band qilmaganini tekshiring.',
      );
      return false;
    }
  }

  function stop() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
  }

  function capture(quality = 0.84): Promise<Blob | null> {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return Promise.resolve(null);
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality));
  }

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  return { videoRef, active, cameraError, start, stop, capture, setCameraError };
}
