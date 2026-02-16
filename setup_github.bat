@echo off
setlocal

echo Git kontrol ediliyor...

REM Git komutunu belirle
where git >nul 2>nul
if %errorlevel% equ 0 (
    set "GIT_CMD=git"
) else (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
        echo Git, standart dizinde bulundu.
    ) else (
        if exist "C:\Program Files (x86)\Git\cmd\git.exe" (
            set "GIT_CMD=C:\Program Files (x86)\Git\cmd\git.exe"
             echo Git, x86 dizininde bulundu.
        ) else (
            echo Git bulunamadi! Lutfen Git'i yukleyin: https://git-scm.com/download/win
            pause
            exit /b
        )
    )
)

echo Kullanilan Git: "%GIT_CMD%"

echo Git kimlik bilgileri kontrol ediliyor...
"%GIT_CMD%" config user.email >nul 2>nul
if %errorlevel% neq 0 (
    echo Git kullanici e-postasi tanimli degil. Lutfen giriniz:
    set /p git_email="E-posta: "
    "%GIT_CMD%" config --global user.email "%git_email%"
)

"%GIT_CMD%" config user.name >nul 2>nul
if %errorlevel% neq 0 (
    echo Git kullanici adi tanimli degil. Lutfen giriniz:
    set /p git_name="Ad Soyad: "
    "%GIT_CMD%" config --global user.name "%git_name%"
)

echo Git deposu baslatiliyor...
if not exist .git (
    "%GIT_CMD%" init
)

echo Dosyalar ekleniyor...
"%GIT_CMD%" add .

echo Degisiklikler kontrol ediliyor...
"%GIT_CMD%" status --porcelain > nul

echo Ilk commit olusturuluyor...
"%GIT_CMD%" commit -m "Proje guncellemesi: Market verileri ve UI iyilestirmeleri" || echo Commit zaten guncel veya olusturulmadi.


echo.
echo GitHub deposu URL'si ayarlaniyor...
set repo_url=https://github.com/yasinkurhan/Hisse-Radar-main
echo Repo URL: %repo_url%

if "%repo_url%"=="" (
    echo URL girilmedi. Islem iptal edildi.
    pause
    exit /b
)

"%GIT_CMD%" branch -M main
"%GIT_CMD%" remote remove origin >nul 2>nul
"%GIT_CMD%" remote add origin %repo_url%
"%GIT_CMD%" remote set-url origin %repo_url%

echo GitHub'a gonderiliyor...
"%GIT_CMD%" push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo Hata olustu. Lutfen su adimlari kontrol edin:
    echo 1. GitHub parolaniz yerine "Personal Access Token" kullandiginizdan emin olun.
    echo 2. Depo URL'sinin dogru oldugundan emin olun.
) else (
    echo.
    echo Islem basariyla tamamlandi!
)

pause
