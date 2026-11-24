# Lab details needed for the Video module: step-by-step guide for the person with lab access

**Purpose:** finish the speech-options record (ADR 0002, PR #98), decision 0012 (Moodle AI features) and the Video design. Everything below is **read-only**: you only look and copy. You do not change, restart or install anything.

## Rules while you do this (please read first)

1. **Never send:** IP addresses, VM names, hostnames, URLs of the lab, usernames, passwords, tokens, API keys, SSH keys or screenshots that show any of them.
2. **Never run or paste** these, because they can print secrets: `docker inspect`, `env`, `printenv`, `cat .env`, `cat` of a whole config file, `ps aux` output (command lines can contain tokens). Print only the specific lines asked for below, and remove anything that looks like an address or a secret before you send it.
3. **Authentication:** write only the **type** ("bearer token", "API key in a header", "none"), never the value.
4. **Audio:** do not send any audio. Do not use learner or faculty audio. If a test request is needed (step A5), use a short clip you record yourself (a few fictional sentences) and reply only "yes" or "no" about the result.
5. If you cannot find something, or you are not allowed to look, write **"not known"**. Please do not guess. Do not run anything that needs `sudo` unless you already have that right and it is your normal job.
6. Write down for each answer **where you found it** (for example "in the compose file", "from `nvidia-smi`", "asked the admin"). It helps me record it correctly.

---

## Part A: the speech (speech-to-text) service

### Step A0: find out how the service runs
Work out whether it runs in Docker or as a normal service. On the lab VM that hosts it:
- `docker ps --format "{{.Names}}  {{.Image}}"` lists running containers and their image names. If the command is not found, it is not Docker.
- `systemctl list-units --type=service | grep -i -E "whisper|asr|speech|transcri"` lists services with those words in their names.
- If neither shows anything, ask the person who set the service up where it lives. Write down only its **name and folder**, not its address.

### A1 and A2: model, size, engine and versions
1. Open the service's folder (the one with `docker-compose.yml`, a `Dockerfile`, a `.service` file or a README).
2. Print only the lines that mention the model: `grep -i -E "model|whisper|faster|ctranslate|cpp" docker-compose.yml` (use the real file name). Look for a model name such as `tiny`, `base`, `small`, `medium`, `large-v3` or `turbo`, with or without `.en` (English-only), and any "distil" in the name.
3. **Engine** is one of: openai/whisper, faster-whisper, whisper.cpp, or something else. The image or package name usually tells you.
4. **Versions:**
   - Python-based: `pip list | grep -i -E "whisper|ctranslate2|faster"`. For a container: `docker exec <container-name> pip list | grep -i -E "whisper|ctranslate2|faster"`.
   - whisper.cpp: the model file name in the models folder (for example `ggml-medium.en.bin`), and `git -C <folder> log -1 --format="%h %cd"` for the code version.
   - An image tag like `:1.2.3` is also a version. Copy it.
5. Report: model name and size, English-only or multilingual, distilled or not, engine, engine version, model version if known.

### A3: hardware and concurrency
- GPU: `nvidia-smi` prints the GPU model and memory. If the command is not found, write "no NVIDIA GPU".
- CPU: `lscpu | head -20`. Memory: `free -h`.
- Concurrency: search the service's config for words like `workers`, `concurrency`, `max_concurrent`, `threads`: `grep -i -E "worker|concurren|thread" <config-file>`. If nothing, write "not known".

### A4: request format, limits and the type of authentication
- If the service has an API documentation page (many Python services have `/docs`), open it from inside the lab and note: the endpoint **path name** (not the address), the audio formats accepted (wav, mp3, m4a, flac…), the field names for the file and for options.
- **Size limit and timeout:** search the proxy or service config: `grep -i -E "client_max_body_size|timeout|max_size|max_upload" <config-file>`. Copy the number and unit.
- **Authentication type:** does a request need a header such as `Authorization: Bearer …` or an API key? Write the type only.

### A5: does it return word-level timestamps?
1. First read the API docs or parameters for words like `word_timestamps`, `timestamp_granularities`, `words`.
2. If the docs do not say, and **you are allowed to call the endpoint**, send **one** request with your own short fictional clip and ask for the detailed output (some services call this `verbose_json`, others a `word_timestamps` flag; use the lab's own documented call).
3. In the reply, look for a list called `words` where each item has a start time and an end time.
4. Report only: "word timestamps: yes" or "no", the **field name**, and how you asked for them. Do not paste the transcript text.

### A6: what the service keeps of the audio
Ask whoever runs the service, and check what you can:
1. Where uploaded files go (a temporary or uploads folder named in the config).
2. After one test request, wait a few minutes and see whether the clip is still in that folder: `ls -l <upload-folder>` (print only file names and times).
3. Whether a cleanup job exists (`crontab -l` for the service user, or a clean-up setting in the config).
4. Whether transcripts or logs keep the text (look for a log folder; print only the file names).
5. Report: "audio kept: yes/no, for how long", "transcript kept: yes/no", "who can read it", or "not known". Do not promise that anything is deleted.

---

## Part B: FFmpeg on the lab image

1. Find out which environment the video pipeline will use (the lab image). If it is a container image: `docker run --rm <image-name> ffmpeg -version` (or, in a running container, `docker exec <container-name> ffmpeg -version`).
2. Copy **all** the output. The first line gives the version. The line starting `configuration:` lists the build options (it matters because it shows whether the build is GPL or LGPL). It contains no secrets.
3. If the command says ffmpeg is not found, write "ffmpeg not installed in that image".

---

## Part C: the Moodle sites (administrator rights needed)

Skip this part if you do not have site administrator rights; say so.

### C1: AI providers, placements and reports (Moodle 5.3)
1. Log in to the **Moodle 5.3** lab site as site administrator.
2. Open **Site administration**, then the **AI** area. (In some versions it is under **General → AI**.)
3. Open **AI providers**. Note each provider listed and whether it is **enabled** or **disabled**.
4. Open **AI placements** (the page that lists where AI features are offered, such as course assistance and the text editor). Note which placements are enabled and which actions each offers (for example summarise, explain, generate text, generate image).
5. Note whether these pages exist: a **policy acceptance report** and a **usage report**.
6. Do not enter any API keys and do not change any setting.

### C2: the exact Moodle version and build
1. In **Site administration**, open **Notifications** (the page the site shows after login or under General).
2. Copy the line with the release and **build number** exactly as shown (for example "5.3.x (Build: …)"). Do not edit it.

### C3: the same on Moodle 4.5 (optional)
Repeat C1 and C2 on the 4.5 site. Say whether the AI section exists there at all.

---

## Part D: BigBlueButton (optional, only if simple)

1. Version: on the BigBlueButton server, `bbb-conf --version`, only if you are allowed to run it.
2. Recording metadata: a finished recording lives under a folder such as `/var/bigbluebutton/published/presentation/<recording-id>/`. List only the **tag names** in its `metadata.xml`: `grep -o "<[A-Za-z_-]*>" metadata.xml | sort -u`. Do not copy meeting names, user names or contents.

---

## Report back: fill in and send as plain text

```
A1 model and size / English-only? / distilled?:
A2 engine, engine version, model version:
A3 hardware (GPU/CPU/memory) and concurrency:
A4 audio formats, size limit, timeout, auth TYPE:
A5 word timestamps (yes/no/not known), field name:
A6 audio kept? how long? transcript kept? who can read?:
B7 ffmpeg -version output (full, including "configuration:"):
C1 AI providers and enabled state; placements and actions; reports present?:
C2 Moodle version and build (5.3):
C3 Moodle 4.5: AI section present? version?:
D BigBlueButton version; metadata.xml tag names:
Where I found each answer / anything not known:
```

Check once more that nothing in your reply is an address, name of a machine, a user name, a token or a key.
