# ADR-002 — Yuz/qo'l tahlili faqat brauzerda (on-device)

**Sana:** 2026-09-19 · **Holat:** qabul qilingan (TZ §1.4, §5.1 dan yozib olindi)

## Kontekst

Bemor videosi — eng sezgir ma'lumot. Serverga video yuborish maxfiylik va tarmoq (hotspot) uchun xavfli.

## Qaror

MediaPipe Tasks Vision (FaceLandmarker + blendshapes, HandLandmarker) `apps/web/src/workers/`
ichida WebWorker'da ishlaydi (15 fps). Serverga faqat 1 Hz agregatsiya qilingan raqamli
metrikalar (`fsi`, `smile_asym`, `attention`, …) 10 tadan batch bo'lib yuboriladi
(`POST /sessions/{id}/face-metrics`). Xom kadr/video hech qachon yuborilmaydi.

## Oqibatlar

- Backend hech qachon rasm/video qabul qilmaydi (P2 MedGemma epikriz/MRT bundan mustasno — faqat klinisist).
- Formulalar (FSI, asimmetriya) deterministik va birlik testlar bilan qoplanadi (T-07).
- Network tab'da tekshiriladi (Acceptance §13).
