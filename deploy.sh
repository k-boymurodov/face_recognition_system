#!/bin/bash
echo "🏦 Bank Davomat Tizimini o'rnatish boshlandi..."

# 0. Proksi sozlamalarini tozalash (Xatolikni oldini olish uchun)
echo "🧹 Noto'g'ri proksi sozlamalari tozalanmoqda..."
git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true
git config --system --unset http.proxy 2>/dev/null || true
git config --system --unset https.proxy 2>/dev/null || true
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# Agar ~/.gitconfig faylida xato satr bo'lsa o'chirish
sed -i '/proxy.example.com/d' ~/.gitconfig 2>/dev/null || true

# 1. Tizim paketlarini yangilash
sudo apt update
sudo apt install -y python3-pip python3-venv libgl1-mesa-glx portaudio19-dev

# 2. Virtual muhit yaratish
python3 -m venv venv
source venv/bin/activate

# 3. Kutubxonalarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt

# Ba'zan face_recognition_models avtomatik o'rnatilmay qolishi mumkin
echo "📦 Qo'shimcha modellarni o'rnatish..."
if [ -f "face_recognition_models-master.zip" ]; then
    echo "📦 Lokal ZIP fayldan o'rnatilmoqda..."
    pip install ./face_recognition_models-master.zip
else
    echo "🌐 GitHub'dan yuklanmoqda..."
    pip install https://github.com/ageitgey/face_recognition_models/archive/master.zip || echo "❌ Internet orqali o'rnatib bo'lmadi. ZIP faylni qo'lda yuklang."
fi

# 4. Ma'lumotlar bazasini sozlash
python3 setup_database.py

# 5. Loglar uchun papka yaratish
mkdir -p logs

echo "✅ O'rnatish muvaffaqiyatli yakunlandi!"
echo "Dasturni ishga tushirish uchun: source venv/bin/activate && python3 quickstart.py"
chmod +x deploy.sh