.PHONY: migrate reset-db up down restart logs

# Run migrations
migrate:
	docker-compose exec backend alembic upgrade head

# Reset database (drop all and recreate)
reset-db:
	docker-compose exec backend ./scripts/reset_db.sh

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f backend

# View all logs
logs-all:
	docker-compose logs -f
