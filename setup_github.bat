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

echo Git deposu baslatiliyor...
"%GIT_CMD%" init

echo Dosyalar ekleniyor...
"%GIT_CMD%" add .

echo Ilk commit olusturuluyor...
"%GIT_CMD%" commit -m "Proje guncellemesi: Market verileri ve UI iyilestirmeleri"

echo.
echo Lutfen GitHub deposu URL'sini yapistirin (Ornek: https://github.com/kullanici/repo.git):
set /p repo_url="URL: "

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
