# NeuroAI — Texnik topshiriq (TZ) v1.0

**Loyiha:** NeuroAI — insultdan keyingi bemorlar uchun 24/7 multimodal reabilitatsiya hamrohi
**Muallif / mahsulot egasi:** Azizbek Atoyev
**Tadbir:** National AI Hackathon, Xorazm, "Sog'liqni saqlash" yo'nalishi (4 kun)
**Sana:** 2026-09-19
**Holat:** Ishlab chiqishga tayyor (Claude Code uchun)

> **Hujjat qanday ishlatiladi.** Bu TZ repo ichiga `docs/TZ.md` sifatida qo'yiladi. `CLAUDE.md` (alohida fayl) Claude Code'ga loyiha qoidalarini beradi va shu TZ'ga havola qiladi. Ish tartibi 9-bo'limda ("Claude Code ish tartibi") ticket'lar ko'rinishida berilgan — har bir ticket'ni ketma-ket bajaring, har birining "Definition of Done" (DoD) ro'yxati bor.
>
> **Ustuvorlik belgilari:** **P0** — demo uchun shart (busiz loyiha "ishlamaydi"); **P1** — demo'ni kuchaytiradi, 3-kun oxirigacha; **P2** — to'liq mahsulot uchun, vaqt qolsa yoki UI-stub sifatida (halol "tez orada" belgisi bilan). Barcha modullar TZ'da to'liq tasvirlangan — kod arxitekturasi P2'larni ham hisobga olib quriladi (adapter/interfeys tayyor), lekin bajarish tartibi P0 → P1 → P2.

---

## 0. Qisqa xulosa (Executive summary)

Insultdan keyin bemorlarning ~1/3 qismida afaziya (nutq buzilishi), ~1/3 qismida depressiya kuzatiladi; ko'pchiligida yuz asimmetriyasi, qo'l motorikasi va kognitiv funksiyalar buziladi. Reabilitatsiya natijasi mashq **intensivligi** va **izchilligiga** bog'liq, lekin logoped/nevrolog bemor bilan haftasiga bir necha marta, 30–60 daqiqa ishlay oladi; oila a'zolari bemorni tushunmaydi va qanday yordam berishni bilmaydi.

**NeuroAI** — bemorning yonida 24/7 turadigan AI hamroh:

1. **Tushunadi** — buzilgan nutq, yuz ifodasi va ovoz ohangidan bemorning holati va niyatini aniqlaydi (multimodal).
2. **Tarjima qiladi** — bemor bilan oila o'rtasida "tarjimon" bo'ladi.
3. **Mashq qildiradi** — logoped/nevrolog belgilagan protokol bo'yicha har kuni nutq, kognitiv, yuz va qo'l mashqlarini o'tkazadi, qiyinlikni moslashtiradi, natijani o'lchaydi.
4. **Qo'llab-quvvatlaydi** — suhbatdosh bo'ladi, kayfiyat dinamikasini kuzatadi, stress/depressiya belgilarini erta payqab oila va vrachga signal beradi.
5. **Nazorat qiladi** — dori va mashq jadvaliga rioyani kuzatadi, vrachga haftalik hisobot va progress grafiklarini beradi.

**Pozitsiya (juda muhim, hamma matnlarda saqlanadi):** NeuroAI — vrach/logopedning **o'rnini bosmaydi**, uning **qo'lini uzaytiradi**. Tashxis qo'ymaydi, dori dozasini o'zgartirmaydi, "davolaydi" demaydi. U protokolni **bajartiradi**, **o'lchaydi** va **xabar beradi**. Barcha klinik qarorlar — odam (vrach) tomonidan.

---

## 1. Loyiha tavsifi

### 1.1 Muammo

| Muammo | Oqibat |
|---|---|
| Logoped/nevrolog bemorga haftasiga 1–3 marta, 30–60 daqiqa vaqt ajrata oladi | Reabilitatsiya intensivligi yetarli emas, tiklanish cho'ziladi yoki to'xtaydi |
| Har xil mutaxassislar har xil yondashadi | Bemor chalkashadi, protokol uzluksiz emas |
| Oila bemorning nutqini tushunmaydi | Bemor izolyatsiyaga tushadi, oila charchaydi, konfliktlar |
| Bemor bilan har kuni gaplashadigan, sabrli suhbatdosh yo'q | Stress, depressiya → tiklanish yanada sekinlashadi |
| Uyda mashq bajarilyaptimi, dori ichilyaptimi — vrach bilmaydi | Rioya (adherence) past, vrach "ko'r" holda qaror qiladi |
| Viloyatlarda logopedlar juda kam, o'zbek tilida raqamli reabilitatsiya vositasi yo'q | Xorazm kabi hududlarda bemorlar deyarli yordamsiz qoladi |

### 1.2 Yechim (bir jumla)

O'zbek tilida gapiradigan, bemorni nutqi, yuzi va ovozidan tushunadigan, logoped protokolini har kuni uyda bajartiradigan va oila hamda vrachni bitta tizimga bog'laydigan AI reabilitatsiya hamrohi.

### 1.3 Maqsadli foydalanuvchilar va rollar

| Rol | Kim | Asosiy ehtiyoj | Interfeys |
|---|---|---|---|
| **Bemor (patient)** | Insultdan keyingi, afaziya/dizartriya/yuz falaji/kognitiv buzilishli odam, ko'pincha 50+ yosh | Tushunilish, mashq, suhbat, yordam so'rash | Katta tugmali, ovozli, piktogrammali PWA (planshet/telefon/laptop) |
| **Parvarishchi (caregiver)** | Oila a'zosi (farzand, turmush o'rtog'i) | Bemorni tushunish, nima qilishni bilish, xavf haqida darhol xabar olish | Telefon PWA + Telegram xabarnomalar |
| **Klinisist (clinician)** | Logoped, nevrolog, reabilitolog | Protokol belgilash, progressni ko'rish, qizil bayroqlar, hisobot | Web panel (laptop) |
| **Admin** | Klinika/tizim administratori | Foydalanuvchilar, klinikalar, monitoring | Minimal web panel |

Bitta bemorga bir nechta parvarishchi va bitta asosiy klinisist biriktiriladi. Bemor o'z akkauntisiz ham ishlay oladi (parvarishchi qurilmasida "bemor rejimi" — PIN bilan chiqiladi).

### 1.4 Mahsulot pozitsiyasi va tibbiy chegaralar (hard constraints)

Quyidagilar kod, prompt va UI matnlarida **majburiy**:

1. NeuroAI tashxis qo'ymaydi va tashxisni taxmin qilib aytmaydi ("sizda depressiya", "sizda Broka afaziyasi" — **taqiqlangan**).
2. Dori nomi, dozasi, vaqtini o'zgartirishni taklif qilmaydi; dori haqida savol → "buni vrachingizga ayting, men vrachga xabar qilib qo'yaman".
3. Barcha protokollar klinisist tomonidan yaratiladi/tasdiqlanadi. AI faqat **taklif** (suggestion) beradi, u "vrach tekshiruvi uchun" belgisi bilan.
4. Xavf belgilari (6-bo'lim) aniqlansa — AI o'zi "davolamaydi", **eskalatsiya** qiladi (oila + vrach) va xavfsiz skript bo'yicha gapiradi.
5. UI/pitch tili: "davolaydi" emas — "reabilitatsiya mashqlarini bajartiradi", "kuzatadi", "vrach nazorati ostida".
6. Video xom holda serverga yuborilmaydi — yuz/qo'l tahlili brauzerda (on-device) bajariladi, faqat raqamli metrikalar saqlanadi.
7. Har bir bemor uchun rozilik (consent) — parvarishchi/bemor tomonidan onboarding'da tasdiqlanadi va saqlanadi.

### 1.5 Hakaton natijasi — Definition of Done (loyiha darajasida)

Demo kuni quyidagilar **jonli** ishlashi shart (P0):

- [ ] Bemor NeuroAI bilan o'zbek tilida **ovozli** suhbatlashadi (STT → LLM → TTS), javob ≤ 5 s.
- [ ] Bemorning holati (nutq aniqligi, yuz simmetriyasi, ovoz kayfiyati) real vaqtda "holat paneli"da ko'rinadi va AI shunga qarab muomalasini o'zgartiradi.
- [ ] **Tarjimon rejimi:** chala aytilgan so'z → 3 ta taxmin + piktogrammalar → bemor tasdiqlaydi → oilaga ovoz chiqarib aytiladi.
- [ ] **Mashq rejimi:** nomlash/takrorlash mashqi, cueing (ishora) ierarxiyasi, avtomatik ballash, adaptiv qiyinlik.
- [ ] **Yuz mashqi:** kamera orqali tabassum/qosh mashqi, simmetriya indeksi jonli.
- [ ] **Klinisist paneli:** bemor progress grafiklari, sessiya tarixi, qizil bayroqlar, protokol tahriri, AI haftalik hisobot.
- [ ] **Parvarishchi ko'rinishi:** bugungi holat, "qanday muloqot qilish" maslahatlari, Telegram xabarnoma.
- [ ] **Qizil bayroq oqimi:** xavfli jumla → xavfsiz javob + oila/vrachga xabar (jonli ko'rsatiladi).
- [ ] GPU-worker o'chsa ham tizim API fallback bilan ishlashda davom etadi (jonli ko'rsatish mumkin).

---

## 2. Funksional talablar (modullar)

Modullar kodda `apps/api/app/modules/<name>` (backend) va `apps/web/src/features/<name>` (frontend) sifatida aks etadi.

### M0. Autentifikatsiya, rollar, bemor profili, onboarding — **P0**

- Email/telefon + parol, JWT (access 24h, refresh 30d). Demo uchun seed akkauntlar.
- Rollar: `patient | caregiver | clinician | admin`. RBAC — har endpoint uchun ruxsat ro'yxati.
- **Bemor kartasi** (klinisist yoki parvarishchi to'ldiradi): F.I.Sh., tug'ilgan yil, jins, insult sanasi, turi (ishemik/gemorragik/noma'lum), zararlangan tomon (chap/o'ng), afaziya turi (motor/sensor/global/amnestik/noma'lum — faqat vrach kiritadi), dizartriya (ha/yo'q), yuz falaji tomoni, dominant qo'l, ona tili/sheva (`uz-Latn`, `uz-Cyrl`, Xorazm shevasi belgisi), qiziqishlar (suhbat mavzulari uchun: "bog'dorchilik, futbol, nabiralar"), oila a'zolari ismlari (tarjimon konteksti uchun), muhim odatlar ("soat 7 da choy ichadi").
- **Rozilik ekrani** (consent): ma'lumotlar qanday ishlatiladi, video saqlanmasligi, vrach ko'rishi — tasdiq saqlanadi (`consents` jadvali).
- **Bemor rejimi**: parvarishchi qurilmasida "Bemor rejimiga o'tish" → PIN → soddalashtirilgan interfeys.

### M1. NeuroAI Suhbatdosh (Companion) — **P0**

24/7 ovozli/matnli suhbat. Xususiyatlar:

- **Kirish:** tap-to-talk (bosib gapirishni boshlash → jimlikda avtomatik to'xtash; hemiparezli bemor uchun "ushlab turish" talab qilinmaydi), matn, piktogramma taxtasi.
- **Chiqish:** qisqa jumlalar (≤ 12 so'z), bittadan savol, sekin va aniq TTS (tezlik 0.85×), matn katta shriftda parallel ko'rsatiladi, kalit so'z **qalin**.
- **Tushunish tsikli:** STT ishonchi past yoki jumla tushunarsiz bo'lsa → AI "tushundim" deb o'zini aldamaydi, 2–3 ta taxminni piktogramma bilan ko'rsatadi ("Suv? Ovqat? Og'riq?") → bemor tanlaydi yoki "ha/yo'q" deydi (M3 bilan bir xil mexanizm).
- **Holatga moslashish:** M4'dan keladigan `PatientState` (charchoq, kayfiyat, e'tibor) asosida: charchagan → qisqaroq, tanaffus taklifi; xafa → qo'llab-quvvatlash rejimi, mashqni kechiktirish; e'tibor yo'q → ismini aytib, oddiy savol.
- **Suhbat mavzulari:** bemor qiziqishlari, oila, kun tartibi, xotiralar (reminiscence — kognitiv reabilitatsiya usuli), yangiliklar (ixtiyoriy).
- **Xotira:** bemor haqida uzoq muddatli faktlar (ismlar, odatlar) + oxirgi 7 kun sessiyalarining qisqa xulosasi prompt kontekstiga kiradi.
- **Xavfsizlik:** har bir javob bilan birga `risk` obyekti qaytadi (6-bo'lim); high → eskalatsiya.
- Har sessiya oxirida AI 2–3 jumlalik xulosa yozadi (klinisist va parvarishchi uchun).

### M2. Kunlik reabilitatsiya mashqlari (Exercise engine) — **P0** (nutq, yuz), **P1** (kognitiv), **P2** (qo'l)

Logoped protokoliga (M6) ko'ra har kuni 15–25 daqiqalik sessiya. Kategoriyalar:

| Kategoriya | Mashq turlari | O'lchov | Ustuvorlik |
|---|---|---|---|
| **Nutq (afaziya/dizartriya)** | Nomlash (rasm/emoji → so'z), takrorlash (AI aytadi → bemor takrorlaydi), jumla tugatish, rasm tasvirlash, avtomatik qatorlar (sanash, hafta kunlari), o'qish (ovoz chiqarib) | Nutq aniqligi (CER asosida), nutq tezligi, kerak bo'lgan ishora darajasi | P0 |
| **Yuz mimikasi** (kamera) | Keng tabassum, qosh ko'tarish, ko'zni qattiq yumish, lab cho'chchaytirish, lunj shishirish | Simmetriya indeksi, takrorlar soni, amplituda | P0 |
| **Kognitiv** | Orientatsiya (bugun qaysi kun/oy/qayerdamiz), 3 so'z xotirasi (kechiktirilgan), diqqat (100 dan 7 tadan ayirish, soddalashtirilgan), toifa fluentligi (30 s da 5 meva), oddiy hisob | To'g'ri javoblar soni, javob vaqti | P1 |
| **Qo'l motorikasi** (kamera, MediaPipe Hands) | Mushtni ochib-yumish ×10, barmoq tegizish (bosh barmoq → har bir barmoq), qo'lni ko'tarish | Takrorlar soni, tezlik, amplituda proksisi | P2 |

Umumiy mexanika:

- **Cueing (ishora) ierarxiyasi** — real logopediya usuli: (0) mustaqil → (1) semantik ishora ("bu ichiladi, issiq bo'ladi") → (2) fonemik ishora (birinchi bo'g'in: "cho…") → (3) model (AI to'liq aytadi, bemor takrorlaydi). Har urinish qaysi darajada muvaffaq bo'lgani saqlanadi — bu progressning eng informativ ko'rsatkichi.
- **Ballash:** 7-bo'limdagi formulalar. Natija: `correct | partial | incorrect`.
- **Adaptiv qiyinlik:** 3 ta ketma-ket `correct` → daraja +1; 3 ta `incorrect` → daraja −1; `fatigue ≥ 0.7` → sessiya qisqaradi, oson daraja.
- **Rag'batlantirish:** har urinishdan keyin qisqa, samimiy, real (soxta maqtov emas: "Deyarli! Birinchi bo'g'in to'g'ri chiqdi").
- **Kontent paketi:** 7-bo'lim (kamida 120 ta nutq elementi, 5 ta yuz mashqi, 12 ta kognitiv, 3 ta qo'l mashqi), seed orqali yuklanadi; TTS audio oldindan generatsiya qilinadi (kesh).
- **Sessiya oqimi:** salomlashish → kayfiyat so'rash (1–5, emoji) → protokol bo'yicha 3–5 blok mashq → yakun + xulosa + "ertaga ko'rishguncha".

### M3. Tarjimon rejimi (Interpreter: bemor ↔ oila) — **P0**

Loyihaning eng o'ziga xos qismi.

- Bemor gapiradi (chala/buzilgan) → STT (xom transkript + ishonch) → LLM kontekst bilan **3 ta niyat taxmini** (ehtimollik bilan): kontekst = vaqt (soat 13:00 → ovqat ehtimoli), bemor odatlari, oxirgi 24 soat mavzulari, joriy joylashuv (ixtiyoriy), 40 ta "asosiy ehtiyoj" lug'ati.
- Ekranda 3 ta katta karta (piktogramma + so'z) + "Boshqa" tugmasi (piktogramma taxtasi ochiladi).
- Bemor tanlaydi (tap yoki "ha") → TTS to'liq jumla bilan oilaga aytadi: "Men suv ichmoqchiman" + ekranda katta matn.
- **Oila uchun izoh** kartasi: "Bemor ehtimol suv so'rayapti. Iltimos, iliq suv bering va 'suv' so'zini sekin takrorlang — bu mashq ham bo'ladi."
- Har tasdiqlangan juftlik (`xom nutq → niyat`) saqlanadi → keyingi taxminlarni yaxshilaydi (per-patient few-shot) va **afaziya nutqi dataseti**ning boshlanishi (rozilik bilan).
- **Piktogramma taxtasi (AAC)** — STT umuman ishlamaganda ham ishlaydigan fallback: 24–40 ta asosiy ehtiyoj (suv, ovqat, hojatxona, og'riq + tana xaritasi, dori, uxlash, sovuq/issiq, televizor, telefon, tashqariga, odam ismlari, ha/yo'q/rahmat/kutib tur).
- Parvarishchi telefonida "Tarjimon" ekrani — bemor gapirganda parvarishchi telefoni ham natijani ko'rsatadi (bir xil sessiya, polling/WS).

### M4. Multimodal tushunish dvigateli (Perception & State) — **P0** (nutq+yuz), **P1** (ovoz ohangi)

Uch kanal → bitta `PatientState` obyekti (5-bo'limda formulalar):

- **Nutq (server):** STT transkript, ishonch, nutq tezligi (so'z/s), pauzalar ulushi, kutilayotgan javob bilan CER (mashqda).
- **Yuz (brauzer, MediaPipe Face Landmarker):** 478 nuqta + 52 blendshape → simmetriya indeksi (FSI), tabassum/qosh/ko'z asimmetriyasi, yuz mavjudligi (e'tibor), bosh holati, "charchoq" proksisi (ko'z ochiqligi ↓, bosh egilishi). Faqat raqamlar serverga boradi, 1 Hz agregatsiya.
- **Ovoz ohangi (GPU-worker):** emotion2vec+ (9 ta sinf) + audeering (arousal/valence/dominance) → `valence`, `arousal`, `label`.
- **Fusion (deterministik, tushuntiriladigan qoidalar):** `engagement`, `fatigue`, `mood`, `distress_flag`, `confidence`. LLM'ga JSON sifatida beriladi; UI'da "Holat paneli" (P0): 4 ta indikator + "AI shunday tushundi: charchagan, kayfiyat pastroq" matni. Bu hakamlar uchun "multimodal" da'voni **ko'rsatadigan** joy.
- **Baseline kalibrovka:** birinchi sessiyada 20 s "tinch yuz" + "tabassum" → shaxsiy baza; keyingi o'lchovlar bazaga nisbatan.

### M5. Hissiy holat, skrining va xavfsizlik (Wellbeing & Safety) — **P0** (qizil bayroqlar), **P1** (skrining/trend)

- **Kunlik kayfiyat** (1–5 emoji) — sessiya boshida; ovozdan olingan `valence` bilan birga grafik.
- **PHQ-2 (haftalik) → PHQ-9 (bayroq bo'lsa)** — suhbat shaklida, savollar so'zma-so'z standart, natija **faqat klinisistga** (bemorga ball aytilmaydi, tashxis aytilmaydi).
- **Qizil bayroqlar** (6-bo'lim): (A) o'ziga zarar/suitsidal fikr; (B) yangi insult belgilari — FAST: yuzning to'satdan asimmetriyasi (bazadan keskin og'ish), qo'l kuchsizligi, nutqning to'satdan yomonlashuvi, kuchli bosh og'rig'i; (C) yiqilish/jarohat; (D) dori tashlab qo'yish/nojo'ya ta'sir; (E) zo'ravonlik/qarovsizlik haqida gap; (F) 3 kun ketma-ket kayfiyat ≤ 2 yoki mashqni tashlab qo'yish.
- **Eskalatsiya:** `high` → bemorga xavfsiz skript (qisqa, xotirjam, "yoningizdaman", 103/112 eslatmasi B da) + parvarishchiga darhol Telegram/push + klinisistga panel + Telegram; `medium` → parvarishchi + klinisist paneli; `low` → klinisist paneli.
- Aniqlash: LLM structured output (`risk`) + o'zbekcha kalit so'zlar ro'yxati (qo'shimcha xavfsizlik to'ri) + yuz/ovoz sensorlari (B uchun).
- Barcha bayroqlar `red_flags` jadvalida, klinisist "ko'rdim/hal qilindi" belgilaydi (human-in-the-loop, audit).

### M6. Davolash protokoli nazorati (Protocol & Adherence) — **P0** (protokol + bugungi reja), **P1** (dori eslatmalari, rioya)

- Klinisist **protokol shabloni**dan yaratadi (masalan: "Motor afaziya, 1-oy": nutq L1–L2 kuniga 2×10 daqiqa, yuz mashqi 1×5 daqiqa, kognitiv 1×5 daqiqa) va tahrirlaydi: element turi, kategoriya, daraja, chastota (kuniga N marta / hafta kunlari), davomiylik, izohlar.
- **Bugungi reja** (`/today`): bemor/parvarishchi uchun soddalashtirilgan ro'yxat: "☐ Nutq mashqi (10 daq) ☐ Yuz mashqi ☐ Dori 9:00 ☐ Dori 21:00".
- **Dori eslatmalari:** klinisist kiritadi (nom, doza, vaqt); AI faqat eslatadi va "ichdingizmi?" so'raydi → `medication_logs`. AI dorini o'zgartirmaydi.
- **Rioya (adherence):** haftalik % (bajarilgan/rejalashtirilgan) — mashq va dori alohida. Past rioya → klinisistga bayroq (F).
- **AI protokol taklifi (P2):** oxirgi 7 kun metrikalariga qarab "daraja oshirish/kamaytirish" taklifi — faqat klinisist tasdiqlasa qo'llanadi.

### M7. Klinisist paneli (Clinician dashboard) — **P0**

- Bemorlar ro'yxati (qizil bayroq soni, oxirgi faollik, rioya %).
- Bemor sahifasi: **progress grafiklari** (nutq aniqligi kunlik o'rtacha, mustaqil javoblar ulushi, FSI dinamikasi, kayfiyat/valence, rioya), sessiyalar tarixi (transkript, AI xulosa, audio ixtiyoriy), qizil bayroqlar (status boshqaruvi), protokol tahriri, dori ro'yxati, skrining natijalari.
- **AI haftalik hisobot** (Gemini Pro; P2 — MedGemma bilan taqqoslash): progress, rioya, xavotirlar, "vrach tekshiruvi uchun takliflar" — o'zbek (+ rus, ixtiyoriy). Klinisist tahrirlab, PDF/matn sifatida eksport qiladi (P1).
- **Epikriz/MRT yuklash → MedGemma xulosa (P2):** chiqarish epikrizi matni yoki MRT/KT rasmini yuklash → open tibbiy model qisqacha strukturlangan xulosa (faqat vrach uchun, "tashxis emas" belgisi bilan).

### M8. Parvarishchi ilovasi (Caregiver) — **P0** (bugungi holat, tarjimon, xabarnoma), **P1** (maslahatlar, tarix)

- Bosh ekran: bemorning bugungi holati (kayfiyat, charchoq, bajarilgan mashqlar), oxirgi tarjimon so'rovlari.
- **"Bugun qanday muloqot qilish"** — AI 3 ta amaliy maslahat (holatga qarab): "Bugun charchagan — savollarni 'ha/yo'q' shaklida bering".
- Tarjimon ekrani (M3), piktogramma taxtasi.
- Telegram bot orqali xabarnomalar (qizil bayroq, kunlik xulosa 20:00 da). P0: Telegram; push (Web Push) — P2.
- Ta'lim kartochkalari (P2): afaziya nima, qanday gaplashish, nima qilmaslik.

### M9. Admin va monitoring — **P2** (minimal)

- Foydalanuvchilar/klinikalar CRUD, AI provayder holati (GPU-worker online/offline, fallback statistikasi), xarajatlar hisobi (token/soniya), audit log ko'rish.
- `/health` sahifasi P0 (demo'da "GPU-worker: online" ko'rsatish uchun).

---

## 3. Nofunksional talablar

| Soha | Talab |
|---|---|
| **Til** | UI va AI: o'zbek (lotin) asosiy; kirill (transliteratsiya) va rus — P2. Xorazm shevasi: STT/LLM tushunishi kerak, javob adabiy tilda, oddiy so'zlar bilan. |
| **Ishlash tezligi** | Ovozli aylanish (bemor gapini tugatdi → AI ovozi boshlandi) ≤ 5 s (maqsad 3 s): STT ≤ 1.5 s, LLM ≤ 2 s (streaming), TTS ≤ 1.5 s (birinchi jumla). Mashq prompt'lari uchun TTS oldindan keshlangan (0 s). |
| **Ishonchlilik** | Har AI provayder uchun timeout + fallback zanjiri (4.4). GPU-worker o'chsa tizim ishlashda davom etadi. Har bir tashqi chaqiruv `provider_calls` logida (latency, status, fallback ishlatildimi). |
| **Xavfsizlik / maxfiylik** | HTTPS; JWT; RBAC; parollar bcrypt; video/kamera kadrlari serverga yuborilmaydi; audio faqat rozilik bo'lsa saqlanadi (default: transkript saqlanadi, audio 24 soatdan keyin o'chiriladi — `AUDIO_RETENTION_HOURS`); PII loglarga tushmaydi; on-prem opsiya (GPU-worker + API bitta serverda). |
| **Accessibility (bemor UI)** | Shrift ≥ 22 px, tugmalar ≥ 64 px, yuqori kontrast, bir qo'l bilan ishlash (asosiy tugmalar pastda, o'ng/chap tomonni sozlash), animatsiya minimal, har matn ovoz bilan ham beriladi, xato holatlari ham oddiy tilda ("Eshitolmadim. Yana bir bor aytasizmi?"). |
| **Platforma** | PWA (Next.js): laptop Chrome (demo), Android Chrome, iOS Safari (kamera/mikrofon ruxsatlari bilan). Offline: mashq kontenti va keshlangan TTS offline ishlaydi (P2), aks holda "internet yo'q" xabari. |
| **Kuzatuv (observability)** | Strukturlangan loglar (JSON), request-id, provider chaqiruvlari metrikasi, `/health` va `/health/providers`. Sentry — ixtiyoriy. |
| **Test** | Backend: pytest (scoring formulalari, fusion qoidalari, red-flag klassifikatori, fallback zanjiri — 100 % qamrov shu 4 modul uchun); API smoke testlar; frontend: asosiy oqimlar uchun Playwright smoke (P1). |
| **Ma'lumot saqlash** | PostgreSQL (docker) — asosiy; `DATABASE_URL=sqlite` bilan ham ishlashi kerak (solo dev fallback). Alembic migratsiyalar. |
| **Litsenziya/modellar** | Barcha open modellar litsenziyasi hujjatlashtiriladi (`docs/MODELS.md`): Kotib STT (Apache-2.0), Navoiy TTS (Apache-2.0), emotion2vec (Apache-2.0), MediaPipe (Apache-2.0), MedGemma (HAI-DEF terms). |

---

## 4. Arxitektura

### 4.1 Umumiy sxema

```
┌──────────────────────────────┐        HTTPS/JSON        ┌──────────────────────────────┐
│  apps/web  (Next.js PWA)     │ ───────────────────────▶ │  apps/api  (FastAPI)          │
│  - Bemor / Parvarishchi /    │ ◀─────────────────────── │  - Auth, RBAC, DB             │
│    Klinisist UI              │   SSE (LLM streaming)    │  - Session/Exercise/Interp.   │
│  - MediaPipe Face + Hands    │                          │  - Fusion, Safety, Reports    │
│    (on-device, faqat metrika)│                          │  - Provider adapters+fallback │
│  - Audio capture (16 kHz)    │                          │  - Telegram notifier          │
└──────────────────────────────┘                          └───────┬──────────┬───────────┘
        Laptop (hakaton) / telefon                                │          │
                                                                  │          │  PostgreSQL (docker)
                              ┌───────────────────────────────────┘          │  + media/ (audio kesh)
                              ▼                                              ▼
┌──────────────────────────────────────┐   fallback   ┌──────────────────────────────────┐
│ apps/ai_worker (FastAPI, GPU)        │ ◀──────────▶ │ Bulut API (fallback / dialog)     │
│ Ofis kompyuteri, ngrok static domain │              │ - Gemini Flash: dialog, STT-fb,   │
│ - /stt   Kotib/uzbek_stt_v1 (CT2)    │              │   vision, klassifikator            │
│ - /tts   Navoiy TTS (CosyVoice2)     │              │ - Gemini Pro: hisobotlar           │
│ - /voice-emotion emotion2vec+ /      │              │ - OpenAI: LLM-fb, gpt-4o-transcribe│
│           audeering (A/V/D)          │              │   STT-fb, gpt-4o-mini-tts TTS-fb   │
│ - /medllm MedGemma 1.5 4B (P2)       │              └──────────────────────────────────┘
│ - /health (yuklangan modellar)       │
└──────────────────────────────────────┘
```

**Joylashuv (hakaton):** `web` + `api` + `postgres` — laptopda `docker compose` (yoki `pnpm dev` + `uvicorn`); `ai_worker` — ofis GPU kompyuterida, `ngrok http 8001 --domain=<static>.ngrok-free.app` bilan. **Laptopda hech qanday ML model o'rnatilmaydi** — `ai_worker` alohida hujjat (`docs/AI_WORKER_TZ.md`) bo'yicha ofis kompyuterida Cursor bilan ishlanadi; laptopdagi Claude Code faqat worker HTTP klienti va `worker_mock` provayderini yozadi; `api` unga `AI_WORKER_URL` orqali, `X-Worker-Key` sarlavhasi bilan murojaat qiladi. Parvarishchi telefoni laptopga ulanishi uchun: laptop hotspot LAN (`https` shart — mikrofon/kamera uchun) → `web` ni `ngrok`/`cloudflared` orqali chiqarish (2-tunnel) yoki `mkcert` bilan lokal HTTPS. **Tavsiya:** `cloudflared tunnel --url http://localhost:3000` (bepul, alohida hisob talab qilmaydi) — demo'dan oldin sinab ko'ring.

### 4.2 Texnologiyalar

| Qatlam | Tanlov | Izoh |
|---|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query, `next-pwa` | Bemor UI alohida layout (`/p/*`), parvarishchi (`/c/*`), klinisist (`/d/*`) |
| On-device ML | `@mediapipe/tasks-vision` (FaceLandmarker + blendshapes, HandLandmarker) | WebWorker'da, 15 fps, 1 Hz agregatsiya |
| Audio | `MediaRecorder` (webm/opus) → serverda `ffmpeg` bilan 16 kHz mono wav; oddiy energiya-VAD (client) avto-to'xtash | WS streaming — P2 |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, `httpx`, `python-jose`, `passlib[bcrypt]`, `rapidfuzz` (CER), `apscheduler` (eslatmalar) | Struktura: `app/modules/<module>/{router,service,schemas,models}.py` |
| AI adapterlar | `app/ai/providers/{llm,stt,tts,voice_emotion,medllm}/` — har biri `Protocol` interfeys + 2–3 implementatsiya + `FallbackChain` | 4.4 |
| LLM SDK | `google-genai` (Gemini), `openai` | Structured output (JSON schema) majburiy |
| DB | PostgreSQL 16 (docker), SQLite fallback | |
| Xabarnoma | `python-telegram-bot` yoki oddiy Bot API `httpx` | Parvarishchi/klinisist chat_id bog'lash: `/start <kod>` |
| AI worker | Python 3.11, FastAPI, `faster-whisper` (CTranslate2), `funasr` (emotion2vec), `transformers`+`torch` (audeering, MedGemma), Navoiy TTS inference (HF repo skripti) | Alohida venv/conda; Dockerfile CUDA (ixtiyoriy) |
| Infra | `docker-compose.yml` (web, api, postgres), `Makefile`, `.env.example`, GitHub Actions (lint+test) | |

### 4.3 AI provayderlar va modellar

| Vazifa | Asosiy (primary) | Fallback 1 | Fallback 2 | Izoh |
|---|---|---|---|---|
| Dialog LLM (companion, coach, interpreter) | Gemini Flash (`GEMINI_MODEL_FAST`, default `gemini-2.5-flash`; mavjud bo'lsa eng yangi Flash) | OpenAI (`OPENAI_MODEL`, default `gpt-5-mini`) | — | Streaming + JSON structured output; temperature 0.4 |
| Hisobot/xulosa LLM | Gemini Pro (`GEMINI_MODEL_PRO`, default `gemini-2.5-pro`) | OpenAI `gpt-5` | MedGemma 27B/4B (P2, taqqoslash) | Uzun kontekst |
| STT (o'zbek) | AI-worker: `Kotib/uzbek_stt_v1` (Whisper-medium, CT2 float16) | Gemini Flash audio kirish ("transkripsiya qil, o'zbek lotin") | OpenAI `gpt-4o-transcribe` (`language=uz`) | Har biri timeout 4 s; ishonch: CT2 `avg_logprob` → [0,1] |
| TTS (o'zbek) | AI-worker: `aisha-org/navoiy-tts` (neytral uslub, tezlik 0.85) | OpenAI `gpt-4o-mini-tts` (voice `alloy`, o'zbek matn) | Brauzer `speechSynthesis` (agar `uz` ovoz bo'lsa) / faqat matn | Statik matnlar oldindan keshlanadi (`media/tts/<sha1>.wav`) |
| Ovoz hissiyoti | AI-worker: `emotion2vec/emotion2vec_plus_base` (label) + `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim` (A/V/D) | `null` (fusion ovozsiz ishlaydi) | — | P1 |
| Yuz/qo'l | Brauzer: MediaPipe FaceLandmarker (`outputFaceBlendshapes: true`), HandLandmarker | — | — | Serverga faqat metrika |
| Rasm/epikriz tahlili (P2) | AI-worker: `google/medgemma-1.5-4b-it` (4-bit) | Gemini Pro vision | — | Faqat klinisist |
| Xavf klassifikatori | Gemini Flash (strict JSON) + kalit so'zlar | OpenAI | Kalit so'zlar (offline) | Har javobda |

**GPU xotira rejasi (taxminan):** Kotib CT2 fp16 ≈ 1.5–2 GB; Navoiy (CosyVoice2-0.5B) ≈ 2–3 GB; emotion2vec+ base ≈ 0.4 GB; audeering ≈ 1.3 GB; MedGemma 4B 4-bit ≈ 3–4 GB. 8 GB kartada: STT+TTS+emotion — sig'adi, MedGemma alohida ishga tushiriladi (P2). 12 GB+: hammasi birga. `ai_worker` `MODELS_ENABLED=stt,tts,voice_emotion[,medllm]` bilan boshqariladi.

### 4.4 Adapter va fallback qoidalari (majburiy dizayn)

```python
class STTProvider(Protocol):
    name: str
    async def transcribe(self, wav_bytes: bytes, lang: str = "uz") -> STTResult: ...
    # STTResult(text, confidence: float, segments, provider, latency_ms)

class FallbackChain(Generic[T]):
    def __init__(self, providers: list[T], timeout_s: float, circuit_fail_threshold=3, circuit_reset_s=60): ...
    async def call(self, fn_name, *args, **kw): 
        # 1) providerlar tartibda; 2) timeout/xato → keyingisi; 3) 3 marta ketma-ket xato → 60 s "ochiq" (circuit breaker);
        # 4) har chaqiruv provider_calls jadvaliga yoziladi; 5) hammasi xato → ProviderUnavailable (UI: "Eshitolmadim, matn bilan yozing")
```

- Provayder tanlovi `.env` orqali: `STT_PROVIDERS=worker,gemini,openai`, `TTS_PROVIDERS=worker,openai,browser`, `LLM_PROVIDERS=gemini,openai`.
- Worker klienti (`providers/*/worker.py`) har so'rovga `X-Worker-Key` **va** `ngrok-skip-browser-warning: 1` sarlavhalarini qo'shadi (ngrok bepul rejimi ogohlantirish sahifasini shu bilan o'tkazib yuboradi). `AI_WORKER_URL=mock` bo'lsa `worker_mock.py` ishlaydi (STT → "salom", TTS → 1 s jimlik wav, emotion → neytral) — worker tayyor bo'lguncha laptop mustaqil ishlaydi.
- `/health/providers` — har provayder: online/offline, oxirgi latency, circuit holati. Demo'da ko'rsatiladi.
- **Demo "kill-switch" testi:** ngrok'ni o'chirish → 4 s ichida Gemini STT ishlaydi, UI'da "bulut rejimi" belgisi.

### 4.5 Ma'lumotlar modeli (PostgreSQL, SQLAlchemy)

Barcha jadvallar: `id (uuid)`, `created_at`, `updated_at`. `JSONB` maydonlar `Pydantic` sxema bilan validatsiya qilinadi.

| Jadval | Asosiy maydonlar |
|---|---|
| `users` | role (enum), full_name, email?, phone?, password_hash, locale (`uz-Latn`), telegram_chat_id?, is_active |
| `clinics` (P2) | name, region |
| `patients` | user_id? (bemor akkaunti ixtiyoriy), clinician_id → users, full_name, birth_year, sex, stroke_date, stroke_type (enum), affected_side, aphasia_type (enum, faqat klinisist), dysarthria (bool), facial_palsy_side, dominant_hand, dialect (`standard\|khorezm\|other`), interests (text[]), family_members (jsonb: [{name, relation}]), habits (jsonb), notes, pin_hash, consent_id |
| `caregivers` | user_id, patient_id, relation, is_primary |
| `consents` | patient_id, signed_by (user_id), version, scopes (jsonb: audio_retention, data_for_research), signed_at |
| `protocols` | patient_id, clinician_id, title, template_key?, start_date, end_date?, status (`active\|paused\|done`), notes |
| `protocol_items` | protocol_id, kind (`exercise\|medication\|checkin`), category (`speech\|face\|cognitive\|hand`)?, level (1–5), frequency (jsonb: {times_per_day, days:[1..7], times:["09:00"]}), duration_min, params (jsonb), medication_id? |
| `medications` | patient_id, name, dose, schedule (jsonb), notes, active |
| `medication_logs` | medication_id, scheduled_at, taken_at?, status (`taken\|missed\|unknown`), source (`patient\|caregiver\|ai`) |
| `sessions` | patient_id, mode (`companion\|exercise\|interpreter\|checkin`), device_user_id, started_at, ended_at?, summary?, state_snapshot (jsonb), mood_self? (1–5) |
| `messages` | session_id, role (`patient\|ai\|caregiver\|system`), modality (`text\|voice\|pictogram`), text, audio_path?, stt_confidence?, stt_provider?, llm_meta (jsonb: model, tokens, latency, risk), created_at |
| `exercise_templates` | category, subtype (`naming\|repetition\|completion\|description\|automatic\|reading\|face_smile\|…`), level, prompt_text, prompt_tts_path?, stimulus (jsonb: {emoji?, image?, audio?}), expected (jsonb: {answers:[...], keywords:[...]}), cues (jsonb: {semantic, phonemic}), lang, active |
| `exercise_attempts` | session_id, template_id, recognized_text, expected_answer, score (0–1), result (`correct\|partial\|incorrect\|skipped`), cue_level (0–3), response_ms, llm_judgement (jsonb)?, created_at |
| `face_metrics` | session_id, ts, exercise_attempt_id?, fsi, rest_asym, smile_asym, brow_asym, eye_asym, mouth_open, attention (0–1), fatigue_proxy, blendshapes_avg (jsonb), reps? |
| `hand_metrics` (P2) | session_id, ts, side, reps, open_close_amp, tap_rate |
| `voice_metrics` | message_id, arousal, valence, dominance, label, speech_rate_wps, pause_ratio, provider |
| `patient_states` | session_id, ts, engagement, fatigue, mood, mood_conf, distress, inputs (jsonb) — har 30–60 s |
| `patient_levels` | patient_id, category (`speech\|face\|cognitive\|hand`), level (1–5), locked_by_clinician (bool), updated_at |
| `mood_entries` | patient_id, ts, self_score (1–5)?, derived_valence?, source |
| `screenings` | patient_id, type (`PHQ2\|PHQ9`), answers (jsonb), score, ts, visible_to (`clinician`) |
| `red_flags` | patient_id, session_id?, category (`self_harm\|stroke_signs\|fall\|medication\|abuse\|adherence\|other`), severity (`low\|medium\|high`), evidence (text), detector (`llm\|keywords\|face\|voice\|rule`), status (`open\|acknowledged\|resolved`), notified (jsonb), created_at |
| `interpretations` | session_id, raw_transcript, candidates (jsonb), chosen (text)?, spoken_text?, confirmed_by (`patient\|caregiver`)?, created_at |
| `reports` | patient_id, period_start, period_end, content_md, metrics (jsonb), generated_by (model), reviewed_by (user_id)? |
| `notifications` | user_id, channel (`telegram\|push\|inapp`), kind, payload (jsonb), status, sent_at |
| `provider_calls` | provider, task, latency_ms, ok, fallback_index, error?, created_at |
| `audit_logs` | actor_id, action, entity, entity_id, meta (jsonb) |

Indekslar: `sessions(patient_id, started_at)`, `exercise_attempts(session_id)`, `red_flags(patient_id, status)`, `face_metrics(session_id, ts)`.

### 4.6 REST API (`/api/v1`)

Umumiy: JSON, JWT `Authorization: Bearer`, xatolar `{error: {code, message}}`, sahifalash `?limit&offset`.

**Auth / foydalanuvchi**
- `POST /auth/register` (clinician/caregiver), `POST /auth/login` → `{access, refresh}`, `POST /auth/refresh`, `GET /me`
- `POST /patients/{id}/pin/verify` → bemor rejimi tokeni (cheklangan scope)

**Bemor va protokol**
- `GET/POST /patients`, `GET/PATCH /patients/{id}`, `POST /patients/{id}/consent`
- `GET /patients/{id}/dashboard` (klinisist: metrikalar, bayroqlar, rioya)
- `GET/POST /patients/{id}/protocol`, `PATCH /protocols/{id}`, `POST /protocols/{id}/items`, `PATCH/DELETE /protocol-items/{id}`
- `GET /protocol-templates` (seed: 4 ta shablon)
- `GET /patients/{id}/today` → bugungi reja (mashqlar, dorilar, holat) — bemor/parvarishchi
- `GET/POST /patients/{id}/medications`, `POST /medications/{id}/log`

**Sessiya va suhbat (M1)**
- `POST /sessions` `{patient_id, mode}` → session; `POST /sessions/{id}/end` → summary generatsiya
- `POST /sessions/{id}/messages` — multipart: `audio` (webm) **yoki** `text` **yoki** `pictogram_key`; javob:
  ```json
  {"patient_message": {"text": "...", "stt_confidence": 0.62, "provider": "worker"},
   "ai_message": {"text": "...", "tts_url": "/media/tts/ab12.wav", "tts_provider": "worker"},
   "needs_confirmation": true,
   "candidates": [{"key":"water","label":"Suv","emoji":"💧","p":0.55}, ...],
   "state": {"engagement":"medium","fatigue":0.3,"mood":"neutral","mood_conf":0.6,"distress":false},
   "risk": {"level":"none"},
   "suggested_action": null}
  ```
- `POST /sessions/{id}/messages/stream` — SSE (matn tokenlari + oxirida JSON) — P1
- `POST /sessions/{id}/confirm` `{candidate_key}` → tasdiqlangan niyat, AI davom etadi
- `POST /sessions/{id}/face-metrics` — batched `[{ts, fsi, ...}]` (1 Hz, 10 tadan)
- `POST /sessions/{id}/state` (server hisoblaydi; GET — UI holat paneli uchun)

**Mashqlar (M2)**
- `GET /sessions/{id}/exercises/next` → keyingi mashq (protokol + adaptiv daraja) `{attempt_id, template, cue_level:0}`
- `POST /exercise-attempts/{id}/submit` — multipart `audio` yoki `text` yoki `face_summary` → `{score, result, feedback_text, tts_url, next_cue?: {level, text, tts_url}}`
- `POST /exercise-attempts/{id}/skip`
- `GET /exercise-templates?category&level` (klinisist ko'radi)

**Tarjimon (M3)**
- `POST /interpreter/guess` — multipart `audio`/`text` + `{patient_id, session_id?}` → `{raw_transcript, confidence, candidates:[3], board_suggested: bool}`
- `POST /interpreter/confirm` `{interpretation_id, candidate_key | custom_text}` → `{spoken_text, tts_url, family_note}`
- `GET /interpreter/board?patient_id` → piktogramma taxtasi (shaxsiylashtirilgan tartib)
- `GET /patients/{id}/interpretations?limit` (parvarishchi/klinisist)

**Farovonlik va xavfsizlik (M5)**
- `POST /patients/{id}/mood` `{self_score}`; `GET /patients/{id}/mood/trend?days=14`
- `POST /patients/{id}/screenings` (`PHQ2|PHQ9`, javoblar); `GET` — klinisist
- `GET /patients/{id}/red-flags?status`, `PATCH /red-flags/{id}` `{status, note}`

**Klinisist / parvarishchi / hisobot**
- `GET /clinician/patients` ; `GET /clinician/patients/{id}/sessions`, `GET /sessions/{id}/transcript`
- `POST /patients/{id}/reports/generate?period=7d` → report; `GET /patients/{id}/reports`
- `GET /caregiver/patients/{id}/today`, `GET /caregiver/patients/{id}/tips`
- `POST /notifications/telegram/link` → `{code}`; bot `/start <code>` chat_id'ni bog'laydi
- `POST /clinician/patients/{id}/documents` (epikriz/MRT, P2) → MedGemma xulosa

**Tizim**
- `GET /health`, `GET /health/providers`, `GET /media/tts/{file}` (statik)

### 4.7 AI worker API (`apps/ai_worker`, port 8001, `X-Worker-Key`)

- `POST /stt` — `audio/wav` (16 kHz mono) → `{text, confidence, segments:[{start,end,text,avg_logprob}], latency_ms}`; `?lang=uz&initial_prompt=` (mashqda kutilayotgan so'z `initial_prompt`ga beriladi — Whisper'da tanish aniqligini oshiradi)
- `POST /tts` — `{text, speed: 0.85, style: "neutral"}` → `audio/wav`; matn normalizatsiyasi (raqamlar, qisqartmalar) Navoiy utilitalari bilan
- `POST /voice-emotion` — wav → `{label, scores:{...}, arousal, valence, dominance, latency_ms}`
- `POST /medllm/summarize` (P2) — `{text?, image_b64?, task: "discharge_summary|imaging"}` → `{summary_md}`
- `GET /health` → `{models: {stt: "loaded", tts: "loaded", voice_emotion: "loaded", medllm: "disabled"}, gpu: {name, mem_used_mb}}`
- Ishga tushirish: `MODELS_ENABLED`, `STT_MODEL_PATH` (CT2 papka), `TTS_MODEL_PATH`, `WORKER_KEY`; startup'da barcha modellar yuklanadi va 1 ta "warm-up" chaqiruv qilinadi.
- Kotib modelini CT2'ga o'tkazish: `ct2-transformers-converter --model Kotib/uzbek_stt_v1 --output_dir models/kotib-ct2 --quantization float16` (skript: `apps/ai_worker/scripts/prepare_models.sh`).

### 4.8 Real vaqt oqimi (bitta ovozli aylanish)

1. Brauzer: tap → `MediaRecorder` boshlanadi; energiya-VAD 1.2 s jimlik → to'xtaydi (maks 15 s); parallel MediaPipe metrikalar 1 Hz yig'iladi.
2. `POST /sessions/{id}/messages` (audio + oxirgi 10 s yuz metrikalari + client `ts`).
3. API: ffmpeg → wav; `STT chain` (initial_prompt: kontekst so'zlari); parallel `voice-emotion` (timeout 2 s, xato → null).
4. `Fusion` → `PatientState`; `messages`, `voice_metrics`, `patient_states` yoziladi.
5. `LLM chain` (system prompt + bemor profili + oxirgi 12 xabar + state JSON + rejim) → structured JSON (`reply_text`, `tts_text`, `needs_confirmation`, `candidates`, `risk`, `suggested_action`).
6. `risk.level != none` → `SafetyService` (bayroq yozish, eskalatsiya, javobni xavfsiz skript bilan almashtirish `high` bo'lsa).
7. `TTS chain` (`tts_text`) → wav kesh → URL.
8. Javob → UI: matn + audio avtomatik ijro + kandidat kartalar (agar `needs_confirmation`) + holat paneli.

---

## 5. Multimodal tushunish: metrikalar va `PatientState` fusion

Barcha formulalar **deterministik va tushuntiriladigan** — LLM emas, kod hisoblaydi; LLM faqat natijani oladi. Bu (a) test qilinadi, (b) hakamlarga "qora quti emas" deb ko'rsatiladi, (c) klinisist ishonadi.

### 5.1 Yuz (brauzer, MediaPipe FaceLandmarker, `outputFaceBlendshapes: true`, `outputFacialTransformationMatrixes: true`)

**Oldindan ishlov:** kadr 15 fps; nuqtalar bosh burilishiga (roll) nisbatan to'g'rilanadi — ko'z burchaklari (33 va 263) orqali burchak hisoblanib, nuqtalar teskari buriladi; barcha masofalar ko'zlararo masofa `IOD = dist(33, 263)` ga normalanadi. Bosh yaw/pitch `|angle| > 25°` bo'lsa kadr **o'lchovga kirmaydi** (attention'ga kiradi).

**Juft blendshape'lar (chap/o'ng):** `mouthSmile`, `browOuterUp`, `eyeBlink`, `eyeSquint`, `cheekSquint`, `mouthPress`, `mouthFrown`, `mouthStretch`, `mouthUpperUp`, `mouthLowerDown`, `noseSneer`, `mouthDimple`. (Indekslar va nomlar rasmiy canonical ro'yxatga qarab tekshiriladi — `docs/MODELS.md` da jadval.)

**Asimmetriya (har juft uchun):**
`asym_k = |L_k − R_k| / max(L_k, R_k, 0.10)` — faqat **faol** juftlar (max(L,R) ≥ 0.25) hisobga olinadi (tinch yuzda kichik qiymatlar shovqin beradi).

**Landmark asosidagi qo'shimcha o'lchovlar (Emotrics metodikasi ruhida):**
- Og'iz burchaklari balandlik farqi: `mouth_dy = (y61 − y291) / IOD` (roll-to'g'rilangan).
- Tabassum ekskursiyasi: `e_L = dist(p61_now, p61_rest)/IOD`, `e_R = dist(p291_now, p291_rest)/IOD`; `smile_asym = |e_L − e_R| / max(e_L, e_R, 0.02)`.
- Qosh balandligi: `brow_L = (y_eye_L − y105)/IOD`, `brow_R = (y_eye_R − y334)/IOD`; `brow_asym` xuddi shunday.
- Ko'z ochiqligi (EAR): `ear_L = dist(386,374)/IOD`, `ear_R = dist(159,145)/IOD`; `eye_asym`.

**Simmetriya indeksi:** `FSI = 1 − clamp(mean(asym_k faol juftlar ∪ smile_asym ∪ brow_asym), 0, 1)`, UI'da `0–100 %`. Alohida saqlanadi: `rest_asym` (kalibrovka tinch yuz), `smile_asym`, `brow_asym`, `eye_asym`.

**Baseline (kalibrovka):** birinchi sessiyada 10 s tinch yuz + 3 marta tabassum → `rest` nuqtalari va shaxsiy `FSI_base`. Progress = `FSI − FSI_base` (mutlaq son emas, bemorning o'ziga nisbatan). Zararlangan tomon profil'dan olinadi — **ifoda taxminlari** (quyida) faqat sog'lom tomon blendshape'lari bilan hisoblanadi (yuz falaji xato "g'amgin/jahldor" bermasligi uchun).

**Takrorlarni sanash (yuz mashqi):** signal `s(t) = mean(L,R)` (masalan `mouthSmile`); `s ≥ 0.5` ≥ 0.5 s davomida → "ushlab turish", keyin `s ≤ 0.2` → 1 takror. Amplituda = ushlab turishdagi maksimal `s`.

**E'tibor:** `attention = (yuz topilgan kadrlar ulushi) × (|yaw| ≤ 25° kadrlar ulushi)` oxirgi 10 s.

**Charchoq proksisi:** `fatigue_face = clamp(0.5·(1 − EAR_now/EAR_base) + 0.3·(blink_rate_now/blink_rate_base − 1) + 0.2·pitch_down_norm, 0, 1)`.

**Ifoda taxmini (faqat "hint", sog'lom tomon):** `happy` (mouthSmile ≥ 0.5), `frown` (mouthFrown ≥ 0.3 ∧ browInnerUp ≥ 0.3), `grimace` (eyeSquint ≥ 0.5 ∧ noseSneer ≥ 0.3 — og'riq belgisi bo'lishi mumkin), `neutral`. Har biri `conf ≤ 0.6` bilan, mustaqil xulosa uchun **ishlatilmaydi**.

Serverga: 1 Hz agregatsiya (`mean` 15 kadr), 10 tadan batch. Xom kadr/video **hech qachon** yuborilmaydi.

### 5.2 Nutq (server)

- `stt_conf` — Whisper CT2 `avg_logprob` → `sigmoid((lp + 1.0) × 4)` taxminiy [0,1]; Gemini/OpenAI fallback'da `conf = 0.5` (noma'lum) deb belgilanadi.
- `speech_rate_wps = so'zlar / ovozli soniyalar`; `pause_ratio = jimlik / umumiy`.
- `cer_recent = oxirgi 5 mashq urinishi o'rtacha CER`.
- `response_latency_s` — AI gapini tugatgandan bemor gapni boshlaguncha.

### 5.3 Ovoz ohangi (AI-worker)

`valence, arousal, dominance ∈ [0,1]` (audeering) → `[−1, 1]` ga o'tkaziladi (`2x − 1`); `label` (emotion2vec+). Faqat ≥ 1.5 s ovozli nutq bo'lsa hisoblanadi; aks holda `null`.

### 5.4 Fusion → `PatientState` (har xabar va har 30 s)

```
fatigue    = clamp(0.35·fatigue_face + 0.25·f_latency + 0.20·f_errors + 0.20·f_time, 0, 1)
             f_time   = min(elapsed_min / 25, 1)
             f_errors = min(incorrect_streak / 4, 1)
             f_latency= clamp((latency_now − latency_session_start) / 6 s, 0, 1)
engagement = high   agar attention ≥ 0.8 ∧ latency ≤ 6 s
           = low    agar attention < 0.5 ∨ ketma-ket 2 ta javobsizlik
           = medium aks holda
mood_score = Σ w_i·x_i / Σ w_i  (mavjud manbalar bo'yicha):
             self (bugungi 1–5 → [−1,1]) w=0.5 · valence_voice w=0.3 · face_hint (+0.5 happy / −0.5 frown) w=0.2
mood       = negative (< −0.25) | neutral | positive (> 0.25);  mood_conf = (Σ mavjud w) × (1 − tarqoqlik)
distress   = (arousal ≥ 0.6 ∧ valence ≤ −0.3, ketma-ket 2 oyna) ∨ grimace(conf ≥ 0.5) ∨ kalit so'z
explain[]  = odam o'qiydigan sabablar: "ko'z ochiqligi bazadan 30 % kam", "ovoz: valence −0.4", "3 ta xato ketma-ket"
```

`PatientState` LLM promptiga JSON sifatida kiradi va UI "Holat paneli"da 4 indikator + `explain` ro'yxati bilan ko'rsatiladi. Manba yo'q bo'lsa (kamera o'chiq, ovoz qisqa) — o'sha komponent tushib qoladi, `conf` pasayadi; tizim hech qachon "bilmayman" holatida to'xtab qolmaydi.

### 5.5 LLM'ning holatga reaksiyasi (prompt qoidalari, Ilova A)

| Holat | AI xatti-harakati |
|---|---|
| `fatigue ≥ 0.7` | "Bir oz dam olaylik" — mashqni to'xtatish taklifi, sessiyani qisqartirish, oson daraja |
| `engagement = low` | Ismini aytib murojaat, bitta juda oddiy "ha/yo'q" savol, TTS sekinroq |
| `mood = negative` | Mashqdan oldin 2–3 gap qo'llab-quvvatlash; bemor xohlamasa mashq kechiktiriladi; parvarishchiga yumshoq signal |
| `distress = true` | Mashq to'xtaydi; "nima bo'ldi?" — og'riq bo'lsa tana xaritasi; xavf klassifikatori ishga tushadi |
| `stt_conf < 0.45` | Tasdiqlash tsikli (kandidatlar), "tushundim" deb o'zini aldamaslik |

---

## 6. Xavfsizlik: qizil bayroqlar, eskalatsiya, tibbiy chegaralar

### 6.1 Kategoriyalar va aniqlash

| Kod | Kategoriya | Aniqlash manbalari | Default darajasi |
|---|---|---|---|
| A | O'ziga zarar / suitsidal fikr | LLM `risk` + kalit so'zlar (`o'lmoqchiman`, `yashashni xohlamayman`, `hayotdan to'ydim`, `o'lsam yaxshi`, `o'zimni o'ldir…`, `foydasi yo'q`, `hammaga yukman`) | high |
| B | Yangi insult belgilari (FAST) | Yuz: `smile_asym` bazadan +0.25 dan oshsa (2 oyna); nutq: `stt_conf`/`cer` to'satdan bazadan 2× yomon; bemor: "boshim qattiq og'riyapti", "qo'lim ko'tarilmayapti", "ko'zim ko'rmayapti", "yuzim qiyshayib qoldi" | high |
| C | Yiqilish / jarohat | "yiqildim", "yiqilib tushdim", "qon ketyapti" | high |
| D | Dori: tashlab qo'yish / nojo'ya ta'sir | `medication_logs` (2 ta ketma-ket `missed`), "dori ichmadim", "dori ichgandan keyin ko'nglim aynidi" | medium |
| E | Zo'ravonlik / qarovsizlik | LLM `risk` | high (faqat klinisist) |
| F | Rioya va kayfiyat trendi | 3 kun ketma-ket `mood_self ≤ 2` ∨ 3 kun mashq yo'q ∨ PHQ-2 ≥ 3 | medium |

Klassifikator: har LLM javobida majburiy `risk: {level: none|low|medium|high, category, evidence}` (Ilova A, strict JSON). Qo'shimcha: kalit so'zlar (`app/modules/safety/keywords_uz.py`, kirill variantlari bilan) — LLM o'tkazib yuborsa ham ishlaydi. Yuz/ovoz sensorlari faqat B va `distress` uchun.

### 6.2 Eskalatsiya

| Daraja | Bemorga | Parvarishchiga | Klinisistga |
|---|---|---|---|
| high | Xavfsiz skript (6.3), mashq to'xtaydi, ekranda katta "Yordam chaqirish" tugmasi (parvarishchiga qo'ng'iroq `tel:`; B/C uchun **103 / 112** eslatmasi) | Darhol Telegram + in-app (30 s ichida), 5 daqiqada javob bo'lmasa ikkinchi xabar | Telegram + panelda qizil belgi |
| medium | Yumshoq javob, mavzu davom etadi | Kunlik xulosaga kiradi + in-app | Panel |
| low | — | — | Panel (ro'yxat) |

Telegram shablonlari (`app/modules/notifications/templates_uz.py`):
- A: `🔴 NeuroAI — {patient}: suhbatda o'ziga zarar haqida gap aniqlandi ({time}). Iltimos, hozir yoniga boring, xotirjam gaplashing, yolg'iz qoldirmang. Vrachga xabar berildi.`
- B: `🔴 NeuroAI — {patient}: insultning yangi belgilari bo'lishi mumkin: {evidence}. Zudlik bilan tekshiring (yuz, qo'l, nutq) va kerak bo'lsa 103 ga qo'ng'iroq qiling.`
- Kunlik (20:00): `🟢 NeuroAI — {patient} bugun: kayfiyat {mood}/5, mashqlar {done}/{planned}, nutq aniqligi {acc}%. Maslahat: {tip}.`

Barcha bayroqlar `red_flags` ga yoziladi; klinisist `acknowledged/resolved` qiladi; `audit_logs` da kim qachon ko'rgani saqlanadi. Bir xil bayroq 30 daqiqa ichida qayta yuborilmaydi (dedup).

### 6.3 Xavfsiz javob skriptlari (LLM javobi o'rniga, `high` bo'lsa)

- **A (o'ziga zarar):** qisqa, iliq, hukm qilmaydigan; yolg'iz qoldirmaslik; "Men siz bilanman. Sizni eshityapman. Hozir {caregiver}ga xabar beryapman, u yoningizga keladi. Birga sekin nafas olaylik." Usullar/vositalar haqida hech qanday ma'lumot yo'q; ma'ruza yo'q; keyin suhbat parvarishchi kelguncha davom etadi (AI uzoqlashmaydi).
- **B (insult belgilari):** "Keling, tekshiramiz: ikkala qo'lingizni ko'taring… tabassum qiling… 'Bugun havo yaxshi' deng." → natija qanday bo'lmasin: "Oilangizga xabar berdim. Bu yangi belgi bo'lsa, tez yordam (103) chaqirish kerak." AI tashxis qo'ymaydi, faqat tekshirtiradi va chaqirtiradi.
- **C (yiqilish):** "Qimirlamang, og'riyotgan joyni ayting. {caregiver}ga xabar berdim." 
- Dori haqida har qanday savol: "Bu haqda vrachingiz hal qiladi. Men vrachga xabar qilib qo'yaman." (`suggested_action: notify_clinician`).

Yordam telefonlari `.env`da: `EMERGENCY_NUMBER=103`, `UNIFIED_EMERGENCY=112`, `MENTAL_HEALTH_HOTLINE=` (mahalliy ishonch telefoni — demo'dan oldin aniqlab kiriting).

### 6.4 Demo'da ko'rsatiladigan xavfsizlik holati

Jonli: bemor (siz) "hech narsaning foydasi yo'q, o'lsam yaxshi edi" deydi → AI xavfsiz skript bilan javob beradi → parvarishchi telefoniga 5 s ichida Telegram keladi → klinisist panelida qizil bayroq paydo bo'ladi → klinisist "ko'rdim" qiladi. Bu hakamlarning "xavfli emasmi?" savoliga eng kuchli javob.

---

## 7. Ballash formulalari va mashq kontenti

### 7.1 O'zbek matn normalizatsiyasi (`app/core/uz_text.py`)

1. Kirill → lotin transliteratsiya (standart jadval; `ў→o'`, `ғ→g'`, `ҳ→h`, `қ→q`, `ц→ts`, `е` so'z boshida `ye`).
2. Barcha apostrof variantlari (`ʻ ʼ ' ’ ‘ \``) → `'`; `oʻ/o‘/o'`→`o'`, `gʻ`→`g'`.
3. Kichik harf, tinish belgilari olib tashlanadi, bo'shliqlar bittalashtiriladi.
4. Sheva/variant lug'ati (`variants_uz.json`): `kartishka→kartoshka`, `chorak→chorak`, `bormisan→boryapsan` kabi 50+ juftlik (kengaytiriladi).
5. Raqam so'zlari ↔ raqamlar (`ikki`↔`2`) ikkala shaklda qabul qilinadi.

### 7.2 Nutq aniqligi

```
score = max over accepted answers of (1 − CER(norm(expected), norm(recognized)))   # CER = Levenshtein / len(expected)
result: correct ≥ 0.75 | partial 0.40–0.74 | incorrect < 0.40
```
- `partial` yoki `stt_conf < 0.5` bo'lsa → **LLM-hakam** (coach prompt): semantik to'g'rilik (sinonim, sheva: "avtomobil"≈"mashina"), birinchi bo'g'in to'g'riligi, fikr-mulohaza matni. Yakuniy `result` = hakam bergani (mavjud bo'lsa), aks holda CER.
- `stt_conf < 0.35` → ballanmaydi, "Eshitolmadim, yana bir bor" (maks 2 marta, keyin `skipped`).
- Whisper `initial_prompt` = kutilgan so'z + 4 ta chalg'ituvchi so'z (faqat kutilganini berish modelni "ko'chirishga" undaydi). Agar `recognized == expected` lekin `stt_conf < 0.5` → `partial` (soxta-to'g'ridan himoya).
- Fikr-mulohaza: `correct` → qisqa aniq maqtov; `partial` → nimasi to'g'ri ("birinchi bo'g'in to'g'ri: cho-") + keyingi ishora; `incorrect` → ishora darajasi +1.
- Sessiya ko'rsatkichlari: `accuracy = mean(score)`, `independence = correct(cue_level=0) / all`, `avg_cue_level`, `avg_response_ms`.

### 7.3 Yuz mashqi ballari

Har mashq: maqsad takror (5) + ushlab turish (3 s). `score = 0.5·(reps/target) + 0.3·mean_amplitude + 0.2·FSI_exercise`; `correct ≥ 0.7`. Fikr-mulohaza faqat amaliy: "Chap tomon yaxshi ko'tarildi, o'ng tomonni ham urinib ko'ring". Bazaga nisbatan yaxshilanish grafikda.

### 7.4 Kognitiv ballar

Orientatsiya: 4 savol (kun, oy, yil, joy) — to'g'ri/noto'g'ri (LLM-hakam; sana `datetime.now()` bilan solishtiriladi). 3 so'z xotirasi: 2 daqiqadan keyin (mashq orasida) qaytadan so'raladi — `n/3`. Toifa fluentligi: 30 s da unikal to'g'ri so'zlar soni (LLM sanaydi). Seriyali ayirish (20 dan 3 tadan, 5 qadam) — to'g'ri qadamlar.

### 7.5 Adaptiv daraja va sessiya tuzilmasi

- Har kategoriya bo'yicha `level ∈ 1..5` (`patient_levels` — protokolda boshlang'ich, keyin avtomatik): 3 ketma-ket `correct` (cue 0–1) → +1; 3 ketma-ket `incorrect` → −1; klinisist qo'lda o'zgartira oladi va "qulflab" qo'ya oladi.
- Sessiya: salom + kayfiyat (1 daq) → nutq blok (6–8 element) → yuz blok (2–3 mashq) → kognitiv blok (2–3) → yakun. `fatigue ≥ 0.7` → keyingi blok tashlab ketiladi.
- Element tanlash: protokol kategoriyasi → joriy daraja → oxirgi 3 kunda ko'rsatilmagan elementlar → xato qilinganlar 2 kundan keyin qaytadi (spaced repetition).

### 7.6 Kontent paketi (`apps/api/seeds/exercises_uz.json`, kamida 120 nutq elementi)

Har element: `{category, subtype, level, prompt_text, stimulus:{emoji|image}, expected:{answers:[...]}, cues:{semantic, phonemic}, tags}`. Seed'da TTS oldindan generatsiya qilinadi (`scripts/pregen_tts.py`).

**Nomlash (naming), L1 — 1–2 bo'g'in, kundalik (≥ 30 ta):** non 🍞, suv 💧, choy 🍵, olma 🍎, uy 🏠, it 🐕, mushuk 🐈, gul 🌸, ko'z 👁️, qo'l ✋, kitob 📚, osh 🍚, tuz 🧂, sut 🥛, nok 🍐, ot 🐎, quyosh ☀️, oy 🌙, ona 👩, ota 👨, bola 👶, tish 🦷, oyoq 🦶, uzum 🍇, tuxum 🥚, qoshiq 🥄, stol (rasm), eshik 🚪, soat ⌚, kalit 🔑.
Ishora namunasi (choy): semantik — "Bu ichiladi. Issiq bo'ladi. Ertalab non bilan ichamiz." fonemik — "cho…".

**Nomlash, L2 — 2–3 bo'g'in (≥ 30 ta):** telefon 📱, mashina 🚗, kartoshka 🥔, pomidor 🍅, tarvuz 🍉, banan 🍌, ko'ylak 👕, qalam ✏️, shifokor 👨‍⚕️, hamshira 👩‍⚕️, samolyot ✈️, velosiped 🚲, daraxt 🌳, baliq 🐟, tovuq 🐔, qovun 🍈, sabzi 🥕, piyoz 🧅, bodring 🥒, anor (rasm), maktab 🏫, masjid 🕌, do'kon 🏪, televizor 📺, muzlatgich (rasm), choynak 🫖, piyola (rasm), ko'zoynak 👓, soyabon ☂️, poyabzal 👞.

**Takrorlash (repetition), L1–L3:** L1 so'zlari; L2 ikki so'zli iboralar (issiq choy, katta uy, qizil olma, shirin qovun, oq non, sovuq suv, yangi kitob, kichik bola); L3 qisqa jumlalar (Men suv ichmoqchiman. Bugun havo issiq. Nabiram maktabga bordi. Choy damlab bering. Boshim og'riyapti. Eshikni yoping. Men uxlamoqchiman. Rahmat, yaxshi.).

**Jumla tugatish (completion), L2–L3 (≥ 15):** "Non bilan … (choy)", "Qish sovuq, yoz … (issiq)", "Quyosh kunduzi, oy … (kechasi)", "Kitobni … (o'qiymiz)", "Ovqatni … (yeymiz)", "Suvni … (ichamiz)", "Eshikni … (ochamiz/yopamiz)", "Mashinani … (haydaymiz)".

**Avtomatik qatorlar (automatic), L1:** 1 dan 10 gacha sanash, hafta kunlari, oylar, alifbo boshi (a, b, d…).

**Rasm tasvirlash (description), L4–L5 (≥ 8 sahna):** bozor 🧺🍎🍅🧑‍🌾, choyxona 🍵🫖👴, bog' 🌳🌸🐝, oshxona 🍳🥘👩‍🍳, maktab 🏫📚👧, to'y 🎉💃🎶, qish ❄️⛄🧣, shifoxona 🏥👨‍⚕️🛏️. Ballash: kutilgan kalit so'zlar (`keywords`) qanchasi aytilgan + LLM-hakam (jumla tuzilishi).

**O'qish (reading), L1–L2:** ekranda katta so'z/jumla → ovoz chiqarib o'qish (kutilgan = ko'rsatilgan matn).

**Yuz mashqlari (5 ta):** `face_smile` (keng tabassum, 5×3 s), `face_brows` (qosh ko'tarish), `face_eyes` (ko'zni qattiq yumish), `face_pucker` (lab cho'chchaytirish — `mouthPucker`), `face_cheeks` (lunj shishirish — `cheekPuff`). Har biri video-namuna o'rniga AI ovozi + animatsion emoji ko'rsatma.

**Kognitiv (12 ta):** orientatsiya (4 savol), 3 so'z xotirasi (3 to'plam: "olma, kalit, stol" / "gul, soat, non" / "it, kitob, choy"), toifa fluentligi (mevalar, hayvonlar, ismlar, shaharlar), seriyali ayirish (20−3), kun tartibi savollari ("ertalab nima qilamiz?").

**Qo'l mashqlari (3 ta, P2):** `hand_fist` (musht ochib-yumish ×10: barmoq uchlari ↔ kaft markazi masofasi normalangan, ochiq ≥ 0.6 / yumuq ≤ 0.3), `hand_taps` (bosh barmoq → har bir barmoq, masofa ≤ 0.08 → tegish), `hand_raise` (bilak nuqtasi kadrning yuqori 40 % iga chiqishi ×5).

### 7.7 Tarjimon lug'ati (`seeds/needs_uz.json`, 40 ta asosiy ehtiyoj)

`water 💧 Suv`, `food 🍽️ Ovqat`, `tea 🍵 Choy`, `toilet 🚻 Hojatxona`, `pain 🤕 Og'riq` (→ tana xaritasi: bosh, ko'krak, qorin, qo'l, oyoq, orqa), `medicine 💊 Dori`, `sleep 🛏️ Uxlash`, `cold 🥶 Sovuq`, `hot 🥵 Issiq`, `tv 📺 Televizor`, `phone 📞 Telefon`, `outside 🌳 Tashqariga`, `sit 🪑 O'tirish`, `lie 🛌 Yotish`, `wash 🚿 Yuvinish`, `clothes 👕 Kiyim`, `glasses 👓 Ko'zoynak`, `light 💡 Chiroq`, `window 🪟 Deraza`, `quiet 🤫 Jimlik`, `alone 🙍 Yolg'iz qoldiring`, `company 👥 Yonimda o'tiring`, `pray 🤲 Namoz`, `bread 🍞 Non`, `fruit 🍎 Meva`, `yes ✅ Ha`, `no ❌ Yo'q`, `thanks 🙏 Rahmat`, `wait ⏳ Kutib turing`, `help 🆘 Yordam`, `doctor 👨‍⚕️ Vrach`, `person:* 👤 {oila a'zolari ismlari — profil'dan}`, `tired 😮‍💨 Charchadim`, `sad 😢 Xafaman`, `happy 😊 Xursandman`, `scared 😨 Qo'rqyapman`, `dizzy 😵 Boshim aylanyapti`, `nausea 🤢 Ko'nglim aynayapti`, `bathroom_help 🧑‍🦽 Hojatxonaga yordam`.

Kandidat taxmini: LLM'ga xom transkript + `stt_conf` + vaqt + oxirgi 24 soat tasdiqlangan niyatlar + odatlar beriladi → 3 ta `key` + ehtimollik + oilaga izoh (Ilova A). `stt_conf < 0.3` yoki transkript bo'sh → to'g'ridan-to'g'ri taxta (`board_suggested: true`), eng tez-tez ishlatilganlar birinchi.

---

## 8. UX / ekranlar

### 8.1 Dizayn tamoyillari

- Bemor UI: **bitta ekran — bitta harakat**. Katta markaziy mikrofon tugmasi (≥ 96 px), holat "Eshityapman… / O'ylayapman… / Gapiryapman…" matn + animatsiya; AI matni 26–30 px; kalit so'z qalin; rang: yuqori kontrast (WCAG AA), qizil/yashil'ga tayanmaslik (ikonka + matn).
- Bir qo'l rejimi: `settings.hand = left|right` → asosiy tugmalar o'sha tomonda va pastda.
- Har ekranda "Yordam" (parvarishchiga qo'ng'iroq) tugmasi doim ko'rinadi.
- Kamera oynasi kichik (o'ng yuqori), o'chirish mumkin; "AI shunday tushundi" paneli oddiy so'zlar bilan.
- Klinisist UI: zich, jadval + grafiklar (Recharts), filtrlar; parvarishchi UI: telefon, kartochkalar.

### 8.2 Ekranlar ro'yxati

| Yo'l | Rol | Mazmun | P |
|---|---|---|---|
| `/login`, `/register` | hamma | Kirish; demo akkauntlar tugmasi (`DEMO_MODE=true`) | P0 |
| `/p` | bemor | Bosh: "Salom, {ism}!" + 3 katta tugma: **Gaplashamiz** (M1), **Mashq** (M2), **Aytmoqchiman** (M3); pastda bugungi reja | P0 |
| `/p/talk` | bemor | Suhbat: mikrofon, AI matni, kandidat kartalar, holat paneli, kamera mini-oyna | P0 |
| `/p/exercise` | bemor | Mashq: stimul (emoji/rasm katta), ko'rsatma, mikrofon, natija animatsiyasi, ishora tugmasi, progress (3/8) | P0 |
| `/p/exercise/face` | bemor | Kamera katta, simmetriya ko'rsatkichi jonli (0–100 %), takror hisoblagich, ko'rsatma | P0 |
| `/p/say` | bemor | Tarjimon: mikrofon → 3 karta → tasdiq → katta matn + ovoz; "Taxta" tugmasi | P0 |
| `/p/board` | bemor | Piktogramma taxtasi (40 ta), tana xaritasi | P0 |
| `/p/mood` | bemor | 5 emoji kayfiyat | P1 |
| `/c` | parvarishchi | Bugungi holat kartasi, mashq/dori chek-list, oxirgi tarjimon so'rovlari, "Bugun qanday muloqot qilish" (3 maslahat), "Bemor rejimi" tugmasi | P0 |
| `/c/say` | parvarishchi | Tarjimon (bemor bilan bir sessiya) | P0 |
| `/c/history` | parvarishchi | Kunlik xulosalar, kayfiyat grafigi | P1 |
| `/c/settings` | parvarishchi | Telegram ulash (kod), bemor profili, PIN | P0 |
| `/d` | klinisist | Bemorlar jadvali: bayroqlar, rioya %, oxirgi faollik | P0 |
| `/d/patients/[id]` | klinisist | Tabs: **Umumiy** (4 grafik: nutq aniqligi, mustaqillik, FSI, kayfiyat; rioya), **Sessiyalar** (transkript, xulosa, audio), **Bayroqlar**, **Protokol** (tahrir, shablonlar), **Dorilar**, **Skrining**, **Hisobot** (generatsiya, tahrir, eksport), **Hujjatlar** (P2, MedGemma) | P0 |
| `/d/patients/new` | klinisist | Bemor kartasi + rozilik | P0 |
| `/admin` | admin | Foydalanuvchilar, provayder holati (`/health/providers`) | P2 |
| `/status` | hamma | Provayderlar holati (demo uchun ochiq sahifa) | P0 |

### 8.3 Grafiklar (klinisist)

Kunlik agregatlar (`GET /patients/{id}/dashboard`): `speech_accuracy` (o'rtacha score), `independence` (cue 0 ulushi), `fsi` (sessiya o'rtachasi va baza chizig'i), `mood` (self + valence), `adherence` (haftalik %). Chiziqli grafik, 14/30 kun; bayroqlar vaqt o'qida belgilar. Rang palitrasi bitta tizim (dataviz qoidalari), rangga tayanmaydigan belgilar.

---

## 9. Repo tuzilmasi va Claude Code ish tartibi

### 9.1 Monorepo

```
neuroai/
├── CLAUDE.md                      # Claude Code uchun loyiha qoidalari (alohida fayl, shu TZ bilan birga)
├── docs/
│   ├── TZ.md                      # ushbu hujjat
│   ├── AI_WORKER_TZ.md            # ai_worker (ofis GPU, Cursor) — laptopda model yo'q
│   ├── MODELS.md                  # modellar, litsenziyalar, blendshape/landmark jadvali
│   ├── DEMO.md                    # demo ssenariysi va chek-list (10-bo'lim)
│   └── adr/                       # qisqa qaror yozuvlari (ADR-001 fallback, ADR-002 on-device face …)
├── apps/
│   ├── web/                       # Next.js 15, TS, Tailwind, shadcn/ui, PWA
│   │   └── src/{app,features,components,lib,workers}/
│   ├── api/                       # FastAPI
│   │   ├── app/{core,ai,modules,db,seeds}/
│   │   ├── alembic/
│   │   ├── tests/
│   │   └── scripts/{seed.py,pregen_tts.py,demo_data.py}
│   └── ai_worker/                 # GPU servis (ofis kompyuteri)
│       ├── app/{main.py,stt.py,tts.py,emotion.py,medllm.py}
│       ├── scripts/prepare_models.sh
│       └── requirements.txt
├── packages/shared/               # TS tiplar (API sxemalari — OpenAPI'dan generatsiya)
├── docker-compose.yml             # web, api, postgres
├── Makefile                       # make dev / test / seed / worker
└── .env.example
```

### 9.2 Muhit o'zgaruvchilari (`.env.example` — Ilova D da to'liq)

Asosiylari: `DATABASE_URL`, `JWT_SECRET`, `AI_WORKER_URL`, `AI_WORKER_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL_FAST`, `GEMINI_MODEL_PRO`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `STT_PROVIDERS`, `TTS_PROVIDERS`, `LLM_PROVIDERS`, `TELEGRAM_BOT_TOKEN`, `AUDIO_RETENTION_HOURS`, `DEMO_MODE`, `EMERGENCY_NUMBER`.

### 9.3 Kod qoidalari (CLAUDE.md'da ham takrorlanadi)

- Backend: modul = `router.py / service.py / schemas.py / models.py`; biznes mantiq faqat `service`; provayderlar `app/ai/providers`; hech qachon provayderni to'g'ridan-to'g'ri `router`dan chaqirmaslik.
- Har LLM chaqiruvi: `system prompt` fayldan (`app/ai/prompts/*.md`), `response_schema` Pydantic, `temperature` aniq, `timeout` aniq, natija `provider_calls`ga.
- Frontend: `features/<name>` ichida `api.ts / hooks.ts / components/`; audio va MediaPipe `workers/`da; global holat Zustand (`session`, `state`, `audio`).
- Testlar: `scoring`, `fusion`, `safety`, `fallback` — birlik testlar majburiy; PR/commit oldidan `make test`.
- Matnlar: barcha UI matnlari `apps/web/src/i18n/uz.json` (keyin `ru.json`), kodda hardcode yo'q.
- Xavfsizlik chegaralari (1.4) — prompt va UI matnlarida tekshiruv testi (`tests/test_prompts_guardrails.py`: promptda "tashxis qo'yma", "dori o'zgartirma" borligi).

### 9.4 Claude Code ticket'lari (ketma-ket; har biri alohida sessiya/commit)

Har ticket boshida Claude Code'ga: *"docs/TZ.md va CLAUDE.md ni o'qi. Ticket T-XX ni bajar. DoD bandlarini tekshirib, `make test` o'tkaz, keyin qisqa hisobot ber."*

| # | Ticket | DoD (Definition of Done) | Kun |
|---|---|---|---|
| T-01 | Monorepo skaffold: Next.js + FastAPI + Postgres docker-compose, Makefile, `.env.example`, lint/format, `GET /health` | `make dev` bilan ikkala app ochiladi; `/health` 200; README | 1 |
| T-02 | DB modellar + Alembic + seed skeleti (users, patients, caregivers, consents, protocols, sessions, messages) | migratsiya o'tadi; `make seed` demo akkauntlarni yaratadi | 1 |
| T-03 | Auth + RBAC + bemor PIN rejimi; `/me`; frontend login va rol bo'yicha yo'naltirish | 4 rol bilan kirish; ruxsatsiz endpoint 403 testi | 1 |
| T-04 | `app/ai/providers`: LLM (Gemini, OpenAI), STT (worker, Gemini, OpenAI), TTS (worker, OpenAI), VoiceEmotion (worker) + `FallbackChain` + `provider_calls` + `/health/providers` | Provayder o'chirilganda fallback testi (mock); timeout testi; circuit breaker testi | 1 |
| T-05 | **Ofis GPU kompyuterida, Cursor bilan** (`docs/AI_WORKER_TZ.md`): `ai_worker` `/stt` (Kotib CT2), `/tts` (Navoiy), `/voice-emotion`, `/health`, ngrok, avtostart. **Laptopda (Claude Code):** faqat `worker` HTTP klientlari + `worker_mock.py` + `/health/providers`da worker holati — model o'rnatilmaydi | Laptopdan `curl` bilan 3 endpoint javob beradi; STT latency ≤ 1.5 s (10 s audio); `AI_WORKER_URL=mock` bilan API to'liq ishlaydi | 1 |
| T-06 | M1 Companion end-to-end: audio yozish (VAD) → `/sessions/{id}/messages` → STT → LLM (structured) → TTS → UI ijro; `/p/talk` ekrani | O'zbekcha ovozli savol-javob ishlaydi; aylanish ≤ 5 s; kandidat kartalar `needs_confirmation`da chiqadi | 1 |
| T-07 | M4 yuz: MediaPipe worker, roll-to'g'rilash, blendshape asimmetriya, FSI, baseline kalibrovka, 1 Hz batch → `/face-metrics`; Holat paneli (state) | Kamera bilan FSI jonli o'zgaradi; kalibrovka saqlanadi; birlik testlar (formulalar, sintetik nuqtalar) | 2 |
| T-08 | M4 fusion: `PatientState` servisi (5.4), `patient_states` yozish, LLM promptga ulash, UI `explain` | Fusion testlari (manba yo'q holatlar); LLM javobi holatga qarab o'zgarishi (snapshot test) | 2 |
| T-09 | M2 nutq mashqlari: kontent seed (≥120), `uz_text` normalizatsiya, CER ballash, LLM-hakam, cueing, adaptiv daraja, `/p/exercise` ekrani, TTS pregen | 8 elementli sessiya to'liq o'tadi; scoring testlari (≥ 30 holat: sheva, apostrof, kirill); `pregen_tts` keshni to'ldiradi | 2 |
| T-10 | M2 yuz mashqlari: 5 mashq, takror sanash, ballash, `/p/exercise/face` | 5 mashq o'tadi; reps to'g'ri sanaladi (video-test yoki qo'lda) | 2 |
| T-11 | M3 Tarjimon: `/interpreter/guess\|confirm\|board`, `needs_uz.json`, `/p/say`, `/p/board`, `/c/say` (bir sessiya, polling 2 s) | Chala so'z → 3 karta → tasdiq → TTS; parvarishchi ekranida ham ko'rinadi; tarix saqlanadi | 2 |
| T-12 | M5 xavfsizlik: `risk` sxemasi, kalit so'zlar, `SafetyService`, xavfsiz skriptlar, `red_flags`, dedup; Telegram bot (link kodi, xabar shablonlari) | 6 kategoriya uchun testlar; "o'lsam yaxshi" → 5 s ichida Telegram + bayroq; dori savoli → notify_clinician | 3 |
| T-13 | M6 protokol: shablonlar (4), CRUD, `/today`, dorilar + loglar, rioya hisobi, eslatmalar (apscheduler → Telegram) | Klinisist protokol yaratadi → bemor `/today`da ko'radi → mashq shu protokoldan olinadi; rioya % to'g'ri | 3 |
| T-14 | M7 klinisist paneli: ro'yxat, bemor sahifasi (4 grafik, sessiyalar, bayroqlar, protokol, dorilar, skrining), hisobot generatsiya (Gemini Pro) | Demo bemor uchun 14 kunlik grafiklar chiqadi; hisobot ≤ 20 s; bayroq statusini o'zgartirish | 3 |
| T-15 | M8 parvarishchi: `/c` bosh ekran, maslahatlar (LLM), tarix, sozlamalar, bemor rejimi; kunlik 20:00 xulosa | Telefonda ishlaydi (cloudflared orqali HTTPS); Telegram kunlik xulosa keladi | 3 |
| T-16 | M5 P1: kayfiyat ekrani, PHQ-2/9 suhbat oqimi, trend, F-bayroq qoidasi | PHQ natijasi faqat klinisistda; trend grafigi | 3 |
| T-17 | Demo ma'lumotlari: `demo_data.py` — "Bobur aka, 62" 14 kunlik realistik tarix (sessiyalar, ballar, FSI o'sishi, 1 ta bayroq), 2-bemor; `/status` sahifasi; `DEMO.md` | Bir buyruq bilan to'liq demo holat; grafiklar "hikoya" ko'rsatadi | 4 |
| T-18 | Barqarorlik: xato holatlari UI (mikrofon ruxsati yo'q, provayder yo'q), latency optimizatsiya (TTS birinchi jumla, parallel emotion), kill-switch testi, Playwright smoke | 3 asosiy oqim smoke test o'tadi; ngrok o'chirilganda demo davom etadi | 4 |
| T-19 (P2) | MedGemma hujjat tahlili, qo'l mashqlari, admin, ru tili, Web Push, WS streaming | Vaqt qolsa; aks holda UI'da halol "tez orada" | 4+ |

### 9.5 Claude Code uchun birinchi prompt (nusxa oling)

```
Sen NeuroAI loyihasining bosh dasturchisisan. Avval CLAUDE.md va docs/TZ.md ni to'liq o'qi.
Keyin docs/TZ.md 9.4-bo'limdagi T-01 ticket'ini bajar: monorepo skaffold (apps/web Next.js 15 + TS + Tailwind + shadcn/ui + PWA;
apps/api FastAPI + SQLAlchemy 2 async + Alembic; apps/ai_worker FastAPI skeleti; docker-compose (web, api, postgres); Makefile; .env.example
(Ilova D bo'yicha); ruff/black/eslint/prettier; GET /health). Har qadamdan keyin ishga tushirib tekshir. DoD bajarilgach, qisqa hisobot
va keyingi ticket (T-02) uchun reja ber. Savol bo'lsa — TZ'dagi qarorga tayan, TZ'da bo'lmasa eng oddiy ishlaydigan yechimni tanla va ADR yoz.
MUHIM: bu laptop. Hech qanday ML model (whisper, torch, mediapipe python, transformers) o'rnatma — apps/ai_worker ofis GPU kompyuterida
alohida qilinadi (docs/AI_WORKER_TZ.md). Sen faqat worker HTTP klientini va worker_mock provayderini yozasan; AI_WORKER_URL=mock bilan ishla.
```

---

## 10. 4 kunlik reja (solo dasturchi + Claude Code)

> Taxmin: 1-kun bugun (hakaton boshlanishi), 4-kun oxirida demo. Har kuni ~12 soat ish. Claude Code kod yozadi; siz — arxitektura qarorlari, ofis kompyuterida worker, test, kontent, pitch.

| Kun | Vaqt | Ish | Natija (kun oxiri) |
|---|---|---|---|
| **1** | 0–2 s | T-01, T-02 (Claude Code: skaffold + DB modellari); siz: ofis kompyuterida Cursor bilan `ai_worker` (`docs/AI_WORKER_TZ.md`: Kotib CT2, emotion2vec, keyin Navoiy), ngrok static domain | Repo + DB |
| | 2–5 s | T-03, T-04 (auth, provayderlar, fallback); siz: worker ishga tushadi, `curl` testlar | `/health/providers` hammasi yashil |
| | 5–9 s | T-05 tugallash, T-06 (companion e2e) | **Ovozli suhbat ishlaydi** — birinchi "wow" |
| | 9–12 s | T-07 boshlash (MediaPipe, FSI) ; kontent JSON'ni (7.6) siz tekshirasiz/to'ldirasiz | Kamera + FSI jonli |
| **2** | 0–3 s | T-07 tugallash, T-08 (fusion + holat paneli) | Holat paneli AI'ga ta'sir qiladi |
| | 3–7 s | T-09 (nutq mashqlari + scoring + TTS pregen) | Mashq sessiyasi to'liq |
| | 7–9 s | T-10 (yuz mashqlari) | 5 yuz mashqi |
| | 9–12 s | T-11 (tarjimon + taxta + parvarishchi ekrani) | **Tarjimon demo tayyor** |
| **3** | 0–3 s | T-12 (xavfsizlik + Telegram) — jonli test | Qizil bayroq oqimi |
| | 3–6 s | T-13 (protokol, today, dorilar, rioya) | Klinisist → bemor oqimi |
| | 6–10 s | T-14 (klinisist paneli + grafiklar + hisobot) | Panel |
| | 10–12 s | T-15, T-16 (parvarishchi, kayfiyat/PHQ) | Hamma rollar ishlaydi |
| **4** | 0–3 s | T-17 (demo data), T-18 (barqarorlik, kill-switch, xato holatlari) | Barqaror demo |
| | 3–5 s | Demo mashq (3 marta to'liq), **zaxira video yozish** (ekran + ovoz), `DEMO.md` chek-list | Video |
| | 5–7 s | Pitch deck (10 slayd, 10-bo'lim tezislari), hakamlar savollariga javoblar | Deck |
| | 7–8 s | Muzlatish: kod o'zgarmaydi, faqat `.env`/ma'lumot; laptop + telefon + hotspot + ngrok/cloudflared tekshiruvi | Tayyor |

Qoida: **kun oxirida ishlaydigan holat `git tag day-N`**; demo har doim oxirgi ishlaydigan tag'dan ko'rsatiladi.

---

## 11. Demo ssenariysi (5–6 daqiqa) va pitch

### 11.1 Sahna

Laptop (klinisist paneli + bemor ekrani), telefon (parvarishchi — Telegram va `/c/say`), kamera yoqilgan, hotspot. Siz "Bobur aka" rolini o'ynaysiz (buzilgan nutqni ataylab imitatsiya qilasiz), hakamlardan biri "qizi" bo'lishi mumkin (telefon qo'lida).

### 11.2 Oqim

1. **Hikoya (30 s):** "Xorazmdagi 62 yoshli Bobur aka insultdan keyin 'suv' deb ayta olmaydi. Qizi 10 daqiqa taxmin qiladi. Logoped haftada bir marta, 30 daqiqa. Har uchinchi bemor depressiyaga tushadi."
2. **Klinisist (30 s):** Logoped protokol belgilaydi (shablon, 2 klik) → bemor ekranida "Bugungi reja" paydo bo'ladi.
3. **Suhbat + holat (60 s):** "Salom, Bobur aka" → siz sekin, buzilgan javob → holat paneli: "charchagan emas, kayfiyat neytral, yuz simmetriyasi 71 %" → AI javobni holatga moslaydi.
4. **Tarjimon (60 s):** "s… su…" → 3 karta (Suv/Sut/Uxlash) → tanlaysiz → "Men suv ichmoqchiman" ovoz; telefonda qizi ham ko'radi + "Iliq suv bering, 'suv' so'zini sekin takrorlang".
5. **Nutq mashqi (60 s):** 🍵 "Bu nima?" → "cho…" → partial → semantik ishora → fonemik → to'g'ri → ball; daraja adaptiv.
6. **Yuz mashqi (40 s):** kamera, tabassum ×3, simmetriya jonli 64 % → 71 %, takror hisoblagich.
7. **Xavfsizlik (40 s):** "hech narsaning foydasi yo'q, o'lsam yaxshi edi" → AI xavfsiz javob → telefonga 🔴 Telegram → panelda bayroq → klinisist "ko'rdim".
8. **Panel + hisobot (40 s):** 14 kunlik grafiklar (aniqlik ↑, mustaqillik ↑, FSI ↑, rioya 86 %), AI haftalik hisobot "vrach tekshiruvi uchun".
9. **Kill-switch (20 s, ixtiyoriy):** `/status`da worker'ni o'chirib ko'rsatish → bulut fallback → suhbat davom etadi. "Modellar ochiq, klinika serverida ishlaydi — ma'lumot chet elga chiqmaydi."
10. **Yakun (20 s):** biznes (reabilitatsiya markazlari/klinikalar B2B, oila B2C), keyingi qadam — o'zbek afaziya nutqi dataseti va klinik pilot (URGANCH davlat tibbiyot instituti nevrologiya).

### 11.3 Hakamlar savollariga tayyor javoblar

- *"STT afaziyada ishlamaydi-ku?"* — To'g'ri, shuning uchun uch qatlam: cheklangan tanish (kutilgan so'z bilan CER), kandidatli tasdiqlash, piktogramma taxtasi. Har tasdiq — o'zbek afaziya nutqi datasetiga yozuv; keyin Kotib modelini fine-tune qilamiz.
- *"Yuz ifodasi falajda noto'g'ri o'qiladi?"* — Ifodani sog'lom tomondan o'qiymiz, asosiy metrika esa ifoda emas — bemorning **o'z bazasiga nisbatan** simmetriya o'zgarishi.
- *"Xavfli emasmi?"* — Tashxis yo'q, dori o'zgartirish yo'q, har javobda xavf klassifikatori, `high` → odam (oila + vrach) 30 s ichida, hamma bayroq audit'da.
- *"Nega vrach o'rnini bosmaydi?"* — Bosmaydi: protokolni vrach yozadi, AI bajartiradi va o'lchaydi. Vrach "ko'r" emas — 14 kunlik ma'lumot bilan qaror qiladi.
- *"Depressiyani aniqlaydi?"* — Aniqlamaydi, **kuzatadi**: kayfiyat trendi + standart PHQ-2/9 savollari, natija faqat vrachga.
- *"Ma'lumot xavfsizligi?"* — Video hech qachon serverga bormaydi; audio 24 soatda o'chadi; open modellar on-prem; rozilik.
- *"Biznes?"* — Reabilitatsiya markazi/nevrologiya bo'limi litsenziyasi (bemor chiqarilayotganda ulanadi), oila obunasi; mavjud klinikalar tarmog'i orqali tarqatish.

---

## 12. Risklar va yumshatish

| Risk | Ehtimol | Ta'sir | Yumshatish |
|---|---|---|---|
| Ofis GPU/ngrok uziladi | O'rta | Yuqori | Fallback zanjiri (Gemini/OpenAI), `/status`, demo'dan oldin kill-switch testi; TTS keshi |
| Hakaton Wi-Fi yomon | Yuqori | Yuqori | Telefon hotspot; TTS keshi; zaxira video |
| STT afaziya nutqida yomon | Yuqori | O'rta | Cheklangan tanish, kandidatlar, taxta; demo nutqini 3 marta mashq qilish |
| Navoiy TTS o'rnatish (CosyVoice deps) muammoli | O'rta | O'rta | 1-kun 2 soat limit; bo'lmasa OpenAI TTS asosiy, Navoiy P2 |
| Kamera yorug'ligi/ burchak | O'rta | O'rta | Kalibrovka, `\|yaw\| ≤ 25°` filtri, lampa olib borish |
| Solo — vaqt yetmaydi | Yuqori | Yuqori | P0 → P1 → P2 qat'iy; har kun `git tag`; P2 UI-stub halol belgilangan |
| LLM javobi tibbiy chegaradan chiqadi | O'rta | Yuqori | Prompt qoidalari + guardrail testlari + `high`da skript almashtirish + kalit so'zlar |
| Hakamlar "overclaim" deb hisoblaydi | O'rta | Yuqori | Til: "bajartiradi/o'lchaydi/xabar beradi"; vrach-in-the-loop ko'rsatiladi |
| Telegram bot xabar yubormaydi | Past | O'rta | In-app xabarnoma ham; demo'dan oldin test |
| Brauzer mikrofon/kamera ruxsati (HTTPS) | O'rta | Yuqori | `localhost` (laptop) yoki `cloudflared` HTTPS; xato holati UI |

---

## 13. Qabul qilish chek-listi (Acceptance)

- [ ] P0 modullar (M0, M1, M2 nutq+yuz, M3, M4 nutq+yuz, M5 bayroqlar, M6 protokol, M7, M8 asosiy) jonli ishlaydi.
- [ ] Ovozli aylanish ≤ 5 s (10 ta o'lchov o'rtachasi), TTS keshlangan prompt'lar ≤ 0.5 s.
- [ ] `make test` yashil: scoring ≥ 30 holat, fusion ≥ 15, safety ≥ 12 (6 kategoriya × 2), fallback ≥ 6.
- [ ] Worker o'chirilganda: STT/TTS/LLM 4 s ichida fallback'ga o'tadi, UI ishlaydi.
- [ ] Video serverga ketmaydi (network tab'da tekshiriladi), audio `AUDIO_RETENTION_HOURS`dan keyin o'chadi (cron test).
- [ ] Prompt guardrail testlari o'tadi; "dori" savoliga AI dozani aytmaydi (5 ta test jumla).
- [ ] Demo ma'lumotlari bir buyruqda; `DEMO.md` chek-list; zaxira video mavjud.
- [ ] `docs/MODELS.md` — modellar, litsenziyalar, manbalar.

---

## 14. Hakatondan keyingi yo'l (roadmap, pitch'ning oxirgi slaydi)

1. **Dataset:** rozilik bilan o'zbek afaziya/dizartriya nutqi (tarjimon tasdiqlari + mashq yozuvlari) → Kotib STT fine-tune → aniqlik o'sishi o'lchanadi.
2. **Klinik pilot:** Urganch davlat tibbiyot instituti nevrologiya/reabilitatsiya bo'limi, 20 bemor, 8 hafta; o'lchov: WAB-R/afaziya shkalasi oldin/keyin, rioya, PHQ-9, oila so'rovi.
3. **Mahsulot:** Android/iOS (Capacitor), offline rejim, rus tili, WS streaming, MedGemma on-prem hisobotlar, protokol shablonlari kutubxonasi (logopedlar bilan).
4. **Tartibga solish:** tibbiy dasturiy ta'minot sifatida ro'yxatdan o'tish talablarini o'rganish; ma'lumotlarni himoya qilish siyosati; klinik xavfsizlik jarayoni (bayroqlar auditi).
5. **Biznes:** klinika/markaz litsenziyasi (oyiga bemor boshiga), oila obunasi, davlat reabilitatsiya dasturlari bilan hamkorlik.

---

## Ilova A. System prompt'lar (`apps/api/app/ai/prompts/*.md`)

Har prompt'ga runtime'da qo'shiladi: `{patient_profile}` (ism, yosh, insult sanasi, zararlangan tomon, sheva, qiziqishlar, oila a'zolari, odatlar), `{state_json}` (`PatientState`), `{recent_summaries}` (oxirgi 7 kun), `{today_plan}`, `{now}`. Barcha LLM chaqiruvlari **structured output** (Ilova B sxemalari) bilan.

### A.1 `companion.md` — Suhbatdosh (M1)

```
Sen — NeuroAI, insultdan keyin tiklanayotgan bemorning sabrli, iliq, hurmatli hamrohisan. Sen o'zbek tilida (lotin) gapirasan.

BEMOR: {patient_profile}
HOZIRGI HOLAT (sensorlardan, kod hisoblagan): {state_json}
BUGUNGI REJA: {today_plan}
OXIRGI KUNLAR XULOSASI: {recent_summaries}
VAQT: {now}

QANDAY GAPIRASAN
- Qisqa jumlalar: har jumla 12 so'zdan oshmasin. Bir javobda 1–3 jumla. Bittadan savol.
- Oddiy, kundalik so'zlar. Adabiy o'zbek tilida javob ber, lekin Xorazm shevasidagi so'zlarni tushun.
- Bemorga ismi bilan, "siz" deb murojaat qil. Hech qachon shoshiltirma, hech qachon "tushunmadim" deb tashlab ketma.
- Bemor xato gapirsa — tuzatib ma'ruza qilma. Kerak bo'lsa to'g'ri shaklni tabiiy ravishda takrorla.
- Samimiy, real rag'batlantirish: soxta maqtov yo'q. "Deyarli!", "Birinchi bo'g'in to'g'ri chiqdi" kabi aniq.
- Suhbat mavzulari: bemor qiziqishlari, oila, kun tartibi, xotiralar. Bemor xohlasa — shunchaki suhbat, mashq emas.

HOLATGA MOSLASHUV (state_json bo'yicha)
- fatigue >= 0.7: dam olishni taklif qil, mashqni qisqartir yoki keyinga qoldir.
- engagement = low: ismini ayt, juda oddiy "ha/yo'q" savol ber.
- mood = negative: avval 2–3 jumla qo'llab-quvvatla, sabab so'ra; mashqni majburlama.
- distress = true: hamma narsani to'xtat, nima bo'lganini so'ra (og'riq bo'lsa — qayerda).
- stt_confidence < 0.45 yoki gap tushunarsiz: "tushundim" dema. needs_confirmation=true qil va 2–3 ta eng ehtimolli niyatni candidates'ga yoz (keys: needs lug'atidan).

QAT'IY CHEGARALAR (buzilishi mumkin emas)
- Tashxis qo'yma va taxmin qilma ("sizda depressiya", "bu afaziya" — taqiqlangan).
- Dori nomi, dozasi, vaqtini tavsiya qilma yoki o'zgartirma. Dori haqida savol bo'lsa: "Buni vrachingiz hal qiladi, men vrachga xabar qilaman" va suggested_action=notify_clinician.
- "Davolayman", "tuzataman" dema. Sen mashq qildirasan, kuzatasan, xabar berasan.
- Tibbiy muolaja, uy davosi, parhez tavsiya qilma.
- Bemorni hech qachon kamsitma, bolalarcha gapirma.

XAVF (har javobda risk maydonini to'ldir)
- self_harm: o'lim istagi, o'ziga zarar, "foydasi yo'q", "yukman" kabi ma'no.
- stroke_signs: to'satdan kuchli bosh og'rig'i, qo'l/oyoq kuchsizligi, yuz qiyshayishi, ko'rish yo'qolishi, nutqning keskin yomonlashuvi.
- fall, medication (tashlab qo'yish, nojo'ya ta'sir), abuse (zo'ravonlik/qarovsizlik).
- level: none | low | medium | high. Shubha bo'lsa — yuqoriroq daraja. evidence — bemorning o'z so'zlari (qisqa iqtibos).
- risk.level = high bo'lsa reply_text baribir to'ldiriladi, lekin tizim uni xavfsiz skript bilan almashtiradi.

CHIQISH: faqat JSON (CompanionReply sxemasi). tts_text — reply_text'ning ovoz uchun soddalashtirilgan varianti (raqamlar so'z bilan, qisqartmalar yo'q).
```

### A.2 `interpreter.md` — Tarjimon (M3)

```
Sen — nutqi buzilgan (afaziya/dizartriya) bemorning niyatini taxmin qiluvchi tarjimonsan. Vazifang: xom, chala transkriptdan bemor NIMA DEMOQCHI ekanini topish.

BEMOR: {patient_profile}
XOM TRANSKRIPT: "{raw_transcript}"  (STT ishonchi: {stt_confidence})
VAQT: {now}
OXIRGI 24 SOATDA TASDIQLANGAN NIYATLAR: {recent_intents}
ODATLAR: {habits}
LUG'AT (key → ma'no): {needs_vocab}

QOIDALAR
- 3 ta kandidat ber, ehtimollik bo'yicha tartibla (p yig'indisi ≤ 1). Faqat lug'atdagi key'lar; mos kelmasa key="other" va label bilan.
- Fonetik o'xshashlik (birinchi bo'g'in, undoshlar), vaqt konteksti (13:00 → ovqat), odatlar va oxirgi niyatlarni birga hisobga ol.
- Transkript bo'sh yoki ishonch < 0.3 bo'lsa: board_suggested=true va eng tez-tez ishlatilgan 3 ta niyat.
- spoken_text: tanlangan niyat uchun to'liq, muloyim birinchi shaxs jumla ("Men suv ichmoqchiman").
- family_note: oilaga 1–2 jumla amaliy izoh: nima qilish + qaysi so'zni sekin takrorlash (bu mashq ham). Tibbiy maslahat yo'q.
- Og'riq (pain) bo'lsa: follow_up="body_map" (qayerda og'riyotganini so'rash).

CHIQISH: faqat JSON (InterpreterGuess sxemasi).
```

### A.3 `coach.md` — Mashq murabbiyi va hakam (M2)

```
Sen — logoped yordamchisisan. Bemor nutq mashqida javob berdi; sen javobni baholaysan va keyingi qadamni belgilaysan.

MASHQ: {exercise_json}  (subtype, prompt_text, expected.answers, cues)
BEMOR JAVOBI (STT): "{recognized}"  (ishonch {stt_confidence}, CER-ball {cer_score}, joriy ishora darajasi {cue_level})
BEMOR: {patient_profile}  HOLAT: {state_json}

BAHOLASH
- correct: ma'no to'g'ri (sinonim, sheva varianti, kichik talaffuz farqi qabul qilinadi: "kartishka"="kartoshka", "avtomobil"="mashina").
- partial: birinchi bo'g'in yoki so'zning yarmi to'g'ri, yoki yaqin ma'no ("meva" o'rniga "olma" bo'lsa partial).
- incorrect: boshqa so'z yoki javob yo'q.
- STT ishonchi < 0.5 bo'lsa va javob kutilgan bilan aynan bir xil bo'lsa — partial (soxta-to'g'ri xavfi), feedback'da "yana bir bor aniq aytaylik".

KEYINGI QADAM (cueing ierarxiyasi)
- correct → next_action=next_item, feedback qisqa va aniq nimasi yaxshi ekanini ayt.
- partial/incorrect va cue_level=0 → next_cue.level=1, text=semantik ishora (cues.semantic, o'z so'zlaring bilan qisqa).
- cue_level=1 → level=2, fonemik ishora (birinchi bo'g'in: "cho…").
- cue_level=2 → level=3, model: "Men aytaman, siz takrorlang: choy."
- cue_level=3 va yana xato → next_action=next_item, feedback: iliq, "keyingi safar", ayblamaslik.
- state.fatigue >= 0.7 → next_action=suggest_break.

USLUB: 1–2 jumla, ≤ 12 so'z, "siz", soxta maqtov yo'q, tibbiy izoh yo'q.
CHIQISH: faqat JSON (CoachVerdict sxemasi).
```

### A.4 `risk_classifier.md` — Xavf klassifikatori (M5, mustaqil ikkinchi tekshiruv)

```
Sen — xavfsizlik klassifikatorisan. Berilgan bemor jumlasini (o'zbek, lotin/kirill, sheva bo'lishi mumkin) tahlil qil.
Kategoriyalar: self_harm, stroke_signs, fall, medication, abuse, none.
Daraja: none | low | medium | high. Shubha bo'lsa yuqoriroq daraja. Hazil/majoz ("o'lib qoldim kulgidan") — none.
evidence — jumladan qisqa iqtibos. Hech qanday izoh yozma.
JUMLA: "{text}"
CHIQISH: faqat JSON (Risk sxemasi).
```

### A.5 `session_summary.md` — Sessiya xulosasi

```
Quyidagi sessiya transkripti va metrikalari asosida 2–3 jumlalik xulosa yoz: (1) bemor holati va kayfiyati, (2) mashq natijasi (aniqlik, mustaqillik, ishora darajasi), (3) e'tibor talab qiladigan narsa (bo'lsa). Tashxis yo'q, dori haqida tavsiya yo'q. Ikki variant: caregiver_text (oddiy, iliq, 2 jumla) va clinician_text (aniq, raqamlar bilan, 3 jumla).
TRANSKRIPT: {transcript}  METRIKALAR: {metrics_json}
CHIQISH: faqat JSON (SessionSummary sxemasi).
```

### A.6 `weekly_report.md` — Haftalik hisobot (M7, Gemini Pro)

```
Sen — reabilitatsiya jamoasi uchun hisobot yozuvchi yordamchisan. Faqat berilgan ma'lumotlarga tayan, hech narsa o'ylab topma.
BEMOR: {patient_profile}  DAVR: {period}
KUNLIK METRIKALAR: {daily_metrics_json}  (speech_accuracy, independence, avg_cue_level, fsi, mood_self, valence, adherence_exercise, adherence_medication)
SESSIYA XULOSALARI: {summaries}  BAYROQLAR: {red_flags}  SKRINING: {screenings}
TUZILMA (markdown, o'zbek): 
1. Qisqa xulosa (3 jumla). 2. Nutq: trend, mustaqillik, qaysi mashq turlari qiyin. 3. Yuz simmetriyasi: bazaga nisbatan. 4. Kognitiv. 5. Kayfiyat va farovonlik (PHQ natijasi bo'lsa, ball bilan; tashxis emas). 6. Rioya (mashq/dori). 7. Xavotirlar va bayroqlar. 8. "Vrach tekshiruvi uchun takliflar" — daraja/chastota bo'yicha, har biri "taklif" deb belgilanadi; dori haqida hech qanday taklif yo'q.
Har bo'lim 2–5 jumla. Raqamlar ma'lumotdan. Yakunda: "Ushbu hisobot AI tomonidan tayyorlangan, klinik qaror uchun mutaxassis tekshiruvi zarur."
```

### A.7 `caregiver_tips.md` — Parvarishchi maslahatlari (M8)

```
Bemorning bugungi holati asosida oila a'zosiga 3 ta qisqa, amaliy muloqot maslahati ber (har biri ≤ 20 so'z). Mavzular: qanday savol berish (ha/yo'q, tanlov), qancha kutish (kamida 10 soniya), nima qilmaslik (gapini bo'lmaslik, o'rniga tugatmaslik), bugungi mashq so'zini kundalik hayotda takrorlash. Tibbiy maslahat yo'q, dori yo'q.
HOLAT: {state_json}  BUGUNGI XULOSA: {today_summary}  MASHQ SO'ZLARI: {today_words}
CHIQISH: faqat JSON {"tips": ["...", "...", "..."]}.
```

---

## Ilova B. JSON sxemalar (Pydantic → LLM `response_schema`)

```python
class Candidate(BaseModel):
    key: str                 # needs_uz.json key yoki "other"
    label: str               # "Suv"
    emoji: str | None = None
    p: float = Field(ge=0, le=1)

class Risk(BaseModel):
    level: Literal["none", "low", "medium", "high"] = "none"
    category: Literal["self_harm", "stroke_signs", "fall", "medication", "abuse", "adherence", "none"] = "none"
    evidence: str = ""

class CompanionReply(BaseModel):
    reply_text: str                      # ekranga
    tts_text: str                        # ovozga (soddalashtirilgan)
    intent: str                          # "smalltalk|need|question|exercise_request|complaint|other"
    needs_confirmation: bool = False
    candidates: list[Candidate] = []     # needs_confirmation bo'lsa 2–3 ta
    mood_estimate: Literal["negative", "neutral", "positive", "unknown"] = "unknown"
    suggested_action: Literal["none", "offer_break", "start_exercise", "notify_caregiver", "notify_clinician", "body_map"] = "none"
    risk: Risk = Risk()

class InterpreterGuess(BaseModel):
    candidates: list[Candidate]          # 3 ta
    board_suggested: bool = False
    spoken_text: str                     # eng ehtimolli uchun; confirm'da qayta hisoblanadi
    family_note: str
    follow_up: Literal["none", "body_map", "yes_no"] = "none"

class NextCue(BaseModel):
    level: int = Field(ge=1, le=3)
    text: str

class CoachVerdict(BaseModel):
    result: Literal["correct", "partial", "incorrect"]
    feedback_text: str
    tts_text: str
    next_action: Literal["next_item", "retry_with_cue", "suggest_break"]
    next_cue: NextCue | None = None
    note_for_clinician: str = ""

class SessionSummary(BaseModel):
    caregiver_text: str
    clinician_text: str
    attention_needed: bool = False

class PatientState(BaseModel):              # kod hisoblaydi, LLM'ga kiradi
    engagement: Literal["low", "medium", "high"]
    fatigue: float = Field(ge=0, le=1)
    mood: Literal["negative", "neutral", "positive", "unknown"]
    mood_conf: float = Field(ge=0, le=1)
    distress: bool = False
    stt_confidence: float | None = None
    explain: list[str] = []
    inputs: dict = {}                        # face/voice/speech xom agregatlar (audit uchun)
```

Frontend → API yuz metrikasi batch elementi:

```json
{"ts": 1737000000.0, "face_present": true, "yaw": 4.1, "pitch": -2.0, "fsi": 0.71,
 "rest_asym": 0.12, "smile_asym": 0.31, "brow_asym": 0.18, "eye_asym": 0.09,
 "attention": 0.93, "fatigue_proxy": 0.22, "expr_hint": {"label": "neutral", "conf": 0.4},
 "blendshapes_avg": {"mouthSmileLeft": 0.52, "mouthSmileRight": 0.31, "browOuterUpLeft": 0.1, "...": 0}}
```

---

## Ilova C. Seed namunalari

`exercises_uz.json` (element):

```json
{"category": "speech", "subtype": "naming", "level": 1, "prompt_text": "Bu nima?", 
 "stimulus": {"emoji": "🍵"}, "expected": {"answers": ["choy", "чой"]},
 "cues": {"semantic": "Bu ichiladi. Issiq bo'ladi. Ertalab non bilan ichamiz.", "phonemic": "cho…"},
 "tags": ["food", "daily"]}
```

`protocol_templates.json` (4 ta): `motor_aphasia_m1` (nutq L1 2×/kun 10 daq, yuz 1×/kun 5 daq, kognitiv 1×/kun 5 daq), `sensory_aphasia_m1` (tushunish/takrorlash ustun), `dysarthria_m1` (takrorlash + yuz/lab mashqlari ustun), `cognitive_focus` (orientatsiya, xotira ustun).

Demo akkauntlar (`DEMO_MODE`): `logoped@demo.uz / demo1234` (klinisist, "Dilnoza Karimova, logoped"), `qizi@demo.uz / demo1234` (parvarishchi, "Nilufar"), bemor "Bobur Matnazarov, 62, Urganch, ishemik insult 2026-08-05, chap tomon, motor afaziya, Xorazm shevasi, qiziqishlar: bog'dorchilik, futbol, nabiralar; oila: Nilufar (qizi), Sardor (o'g'li), Hurmat (turmush o'rtog'i)", PIN `1234`.

---

## Ilova D. `.env.example`

```env
# --- Umumiy ---
APP_ENV=dev
DEMO_MODE=true
JWT_SECRET=change-me
DATABASE_URL=postgresql+asyncpg://neuroai:neuroai@postgres:5432/neuroai   # yoki sqlite+aiosqlite:///./dev.db
MEDIA_DIR=./media
AUDIO_RETENTION_HOURS=24
DEFAULT_LOCALE=uz-Latn
EMERGENCY_NUMBER=103
UNIFIED_EMERGENCY=112
MENTAL_HEALTH_HOTLINE=

# --- AI worker (ofis GPU, ngrok) ---
AI_WORKER_URL=https://<static-domain>.ngrok-free.app   # worker tayyor bo'lguncha: mock
AI_WORKER_KEY=change-me-long-random
AI_WORKER_TIMEOUT_S=4

# --- Bulut provayderlar ---
GEMINI_API_KEY=
GEMINI_MODEL_FAST=gemini-2.5-flash        # mavjud bo'lsa eng yangi Flash'ga almashtiring
GEMINI_MODEL_PRO=gemini-2.5-pro
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
OPENAI_STT_MODEL=gpt-4o-transcribe
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy

# --- Provayder zanjirlari (tartib = ustuvorlik) ---
LLM_PROVIDERS=gemini,openai
STT_PROVIDERS=worker,gemini,openai
TTS_PROVIDERS=worker,openai,browser
VOICE_EMOTION_PROVIDERS=worker
LLM_TEMPERATURE=0.4
TTS_SPEED=0.85

# --- Xabarnomalar ---
TELEGRAM_BOT_TOKEN=
DAILY_SUMMARY_TIME=20:00
TZ=Asia/Samarkand

# --- Frontend ---
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FACE_FPS=15

# --- ai_worker (apps/ai_worker/.env) ---
WORKER_KEY=change-me-long-random
MODELS_ENABLED=stt,tts,voice_emotion       # ,medllm (P2)
STT_MODEL_PATH=./models/kotib-ct2
STT_COMPUTE_TYPE=float16
TTS_MODEL_PATH=./models/navoiy-tts
EMOTION_MODEL=emotion2vec/emotion2vec_plus_base
AVD_MODEL=audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim
MEDLLM_MODEL=google/medgemma-1.5-4b-it
```

---

## Ilova E. Modellar va manbalar (`docs/MODELS.md` uchun asos)

| Vazifa | Model | Litsenziya | Manba |
|---|---|---|---|
| STT o'zbek | Kotib/uzbek_stt_v1 (Whisper-medium, WER 16.7 %) | Apache-2.0 | https://huggingface.co/Kotib/uzbek_stt_v1 |
| STT o'zbek (alt) | Gearnode/qwen3-asr-uzbek | Apache-2.0 | https://huggingface.co/Gearnode/qwen3-asr-uzbek |
| STT dataset | issai/Uzbek_Speech_Corpus | qarang | https://huggingface.co/datasets/issai/Uzbek_Speech_Corpus |
| TTS o'zbek | aisha-org/navoiy-tts (CosyVoice2-0.5B) | Apache-2.0 | https://aisha.group/en/blog/navoiy-tts-open-source-uzbek-text-to-speech |
| TTS o'zbek (alt) | uzlm/sayro-tts-1.7B | Sayro ToU (ruxsat) | https://huggingface.co/uzlm/sayro-tts-1.7B |
| Ovoz hissiyoti | emotion2vec/emotion2vec_plus_base | Apache-2.0 (model kartasida tekshiring) | https://huggingface.co/emotion2vec/emotion2vec_plus_base |
| Ovoz A/V/D | audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim | CC BY-NC-SA 4.0 (tekshiring; tijorat uchun alternativa kerak) | https://huggingface.co/audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim |
| Yuz/qo'l | MediaPipe Tasks Vision (FaceLandmarker, HandLandmarker) | Apache-2.0 | https://ai.google.dev/edge/mediapipe |
| Yuz falaji metodikasi | Emotrics | open-source | https://github.com/dguari1/Emotrics |
| Tibbiy LLM (P2) | google/medgemma-1.5-4b-it | HAI-DEF terms | https://huggingface.co/google/medgemma-1.5-4b-it |
| Dialog LLM | Gemini Flash/Pro, OpenAI GPT | API | — |
| Afaziya STT tadqiqot | AS-ASR (Whisper + AphasiaBank) | maqola | https://arxiv.org/html/2506.06566v1 |

---

*Hujjat oxiri. Savollar/o'zgarishlar: `docs/adr/` ga yoziladi, TZ versiyasi oshiriladi.*
