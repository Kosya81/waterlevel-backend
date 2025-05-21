# Развертывание на AWS Lightsail

## 1. Создание инстанса в AWS Lightsail

1. Войдите в AWS Console
2. Перейдите в Lightsail
3. Нажмите "Create instance"
4. Выберите:
   - Platform: Linux/Unix
   - Blueprint: Ubuntu
   - Instance plan: $3.50 (512MB RAM, 1 vCPU, 20GB SSD)
5. Нажмите "Create instance"

## 2. Подключение к серверу

1. В Lightsail Console найдите ваш инстанс
2. Нажмите на кнопку "Connect using SSH"
3. Сохраните приватный ключ (.pem файл) в безопасном месте

## 3. Настройка домена (опционально)

1. Купите домен (например, на Namecheap или GoDaddy)
2. В DNS настройках добавьте A-запись, указывающую на IP вашего Lightsail инстанса
3. Подождите обновления DNS (может занять до 24 часов)

## 4. Развертывание приложения

1. Скопируйте файлы на сервер:
```bash
scp -i your-key.pem -r ./* ubuntu@your-instance-ip:/var/www/waterlevel/
```

2. Подключитесь к серверу:
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. Сделайте скрипт настройки исполняемым:
```bash
chmod +x /var/www/waterlevel/scripts/setup_server.sh
```

4. Запустите скрипт настройки:
```bash
cd /var/www/waterlevel
./scripts/setup_server.sh
```

5. Отредактируйте файл .env:
```bash
nano .env
```
Установите правильные значения для:
- POSTGRES_PASSWORD
- POSTGRES_HOST (localhost)
- POSTGRES_USER (waterlevel)
- POSTGRES_DB (waterlevel)

## 5. Настройка SSL (если есть домен)

1. Отредактируйте скрипт setup_server.sh
2. Замените your-domain.com на ваш домен
3. Замените your-email@example.com на ваш email
4. Перезапустите скрипт

## 6. Проверка работы

1. Проверьте статус сервисов:
```bash
sudo systemctl status waterlevel-scheduler
sudo systemctl status waterlevel-api
```

2. Проверьте логи:
```bash
sudo journalctl -u waterlevel-scheduler
sudo journalctl -u waterlevel-api
```

3. Проверьте API:
```bash
curl http://localhost:8000/docs
```

## 7. Обновление приложения

1. Скопируйте новые файлы:
```bash
scp -i your-key.pem -r ./* ubuntu@your-instance-ip:/var/www/waterlevel/
```

2. Перезапустите сервисы:
```bash
sudo systemctl restart waterlevel-scheduler
sudo systemctl restart waterlevel-api
```

## 8. Мониторинг

1. В Lightsail Console можно мониторить:
   - CPU использование
   - Сетевой трафик
   - Дисковое пространство

2. Логи приложения:
```bash
sudo journalctl -u waterlevel-scheduler -f
sudo journalctl -u waterlevel-api -f
```

## 9. Резервное копирование

1. В Lightsail Console можно настроить автоматические снапшоты
2. Рекомендуется делать снапшоты раз в день
3. Хранить снапшоты можно до 7 дней бесплатно 