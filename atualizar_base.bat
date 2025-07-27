@echo off
cd "C:\Users\glaudoberto.filho\Desktop\Projetos Python\app_fup_frontend"

REM Garante que estamos na branch principal
git checkout main

REM Adiciona o arquivo atualizado
git add Atendimento.xlsx

REM Cria commit com mensagem automática
git commit -m "Atualização manual da base Atendimento.xlsx"

REM Envia para o repositório remoto
git push origin main

echo.
echo ✅ Base Atendimento.xlsx atualizada com sucesso!
pause
