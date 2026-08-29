# Majestic AI Fisher

Нативное Windows-приложение на C++17 для анализа интерфейса рыбалки в реальном
времени. Интерфейс, захват экрана, прямой ввод и DQN-модель работают без Python.

## Сборка

Откройте проект в CLion либо выполните CMake с установленным компилятором C++:

```powershell
cmake -S . -B native-build
cmake --build native-build --config Release
```

Запуск: `native-build\MajesticAIFisher.exe`.

Нативная модель сохраняется рядом с программой как `dqn_model.bin`. Старый
`dqn_model.pth` — формат PyTorch/Python и не загружается напрямую C++-версией.
