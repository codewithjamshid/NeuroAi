// MediaPipe FaceLandmarker loader + throttled detectForVideo loop (TZ §5.1, ADR: browser-only,
// frames never leave the device). Imported only from the face page (dynamic, ssr:false).
import type { FaceLandmarker, FaceLandmarkerResult } from "@mediapipe/tasks-vision";

import type { Blendshapes, CameraErrorCode, Point } from "./types";

export const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";
export const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

export class FaceError extends Error {
  readonly code: CameraErrorCode;
  constructor(code: CameraErrorCode, cause?: unknown) {
    super(code);
    this.name = "FaceError";
    this.code = code;
    if (cause !== undefined) this.cause = cause;
  }
}

let landmarkerPromise: Promise<FaceLandmarker> | null = null;

export function loadFaceLandmarker(): Promise<FaceLandmarker> {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
      const fileset = await FilesetResolver.forVisionTasks(WASM_URL);
      const create = (delegate: "GPU" | "CPU") =>
        FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: MODEL_URL, delegate },
          runningMode: "VIDEO",
          numFaces: 1,
          outputFaceBlendshapes: true,
          outputFacialTransformationMatrixes: true,
        });
      try {
        return await create("GPU");
      } catch {
        return await create("CPU");
      }
    })().catch((e: unknown) => {
      landmarkerPromise = null;
      throw new FaceError("model_failed", e);
    });
  }
  return landmarkerPromise;
}

export function mapCameraError(e: unknown): CameraErrorCode {
  if (e instanceof FaceError) return e.code;
  const name = e instanceof DOMException || e instanceof Error ? e.name : "";
  if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") {
    return "cam_denied";
  }
  if (
    name === "NotFoundError" ||
    name === "DevicesNotFoundError" ||
    name === "OverconstrainedError" ||
    name === "NotReadableError"
  ) {
    return "no_cam";
  }
  return "not_supported";
}

export async function openCamera(): Promise<MediaStream> {
  if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
    throw new FaceError("not_supported");
  }
  try {
    return await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
    });
  } catch (e) {
    throw new FaceError(mapCameraError(e), e);
  }
}

export function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((tr) => tr.stop());
}

export type RawFrame = {
  t: number; // performance.now() ms
  landmarks: Point[] | null;
  blendshapes: Blendshapes | null;
  matrix: number[] | null;
  aspect: number;
};

export function toRawFrame(result: FaceLandmarkerResult, t: number, aspect: number): RawFrame {
  const landmarks = result.faceLandmarks?.[0] ?? null;
  const cats = result.faceBlendshapes?.[0]?.categories;
  let blendshapes: Blendshapes | null = null;
  if (cats) {
    blendshapes = {};
    for (const c of cats) blendshapes[c.categoryName] = c.score;
  }
  const matrix = result.facialTransformationMatrixes?.[0]?.data ?? null;
  return { t, landmarks, blendshapes, matrix, aspect };
}

// requestAnimationFrame loop throttled to `fps` (NEXT_PUBLIC_FACE_FPS, default 15).
export function startDetectionLoop(
  landmarker: FaceLandmarker,
  video: HTMLVideoElement,
  fps: number,
  onFrame: (frame: RawFrame) => void,
): () => void {
  const interval = 1000 / Math.max(1, fps);
  let last = -Infinity;
  let lastVideoTime = -1;
  let raf = 0;
  let stopped = false;
  const tick = () => {
    if (stopped) return;
    raf = requestAnimationFrame(tick);
    const now = performance.now();
    if (now - last < interval) return;
    if (video.readyState < 2 || !video.videoWidth || video.currentTime === lastVideoTime) return;
    lastVideoTime = video.currentTime;
    last = now;
    let result: FaceLandmarkerResult;
    try {
      result = landmarker.detectForVideo(video, now);
    } catch {
      return;
    }
    onFrame(toRawFrame(result, now, video.videoWidth / video.videoHeight));
  };
  raf = requestAnimationFrame(tick);
  return () => {
    stopped = true;
    cancelAnimationFrame(raf);
  };
}
