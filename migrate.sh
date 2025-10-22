#!/bin/bash
# Database Migration Helper Script

set -e

source venv/bin/activate

case "$1" in
    create)
        if [ -z "$2" ]; then
            echo "❌ Error: Migration message required"
            echo "Usage: ./migrate.sh create \"your migration message\""
            exit 1
        fi
        echo "🔄 Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        ;;
    up)
        echo "⬆️  Applying migrations..."
        alembic upgrade head
        ;;
    down)
        if [ -z "$2" ]; then
            echo "⬇️  Rolling back last migration..."
            alembic downgrade -1
        else
            echo "⬇️  Rolling back $2 steps..."
            alembic downgrade -$2
        fi
        ;;
    history)
        echo "📜 Migration history:"
        alembic history
        ;;
    current)
        echo "📍 Current migration:"
        alembic current
        ;;
    reset)
        echo "⚠️  WARNING: This will reset all migrations!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🔄 Resetting database..."
            alembic downgrade base
            echo "✅ Database reset complete"
        else
            echo "❌ Reset cancelled"
        fi
        ;;
    *)
        echo "Database Migration Helper"
        echo ""
        echo "Usage: ./migrate.sh <command> [options]"
        echo ""
        echo "Commands:"
        echo "  create <message>    Create new migration"
        echo "  up                  Apply all pending migrations"
        echo "  down [steps]        Rollback migrations (default: 1)"
        echo "  history             Show migration history"
        echo "  current             Show current migration"
        echo "  reset               Reset all migrations (dangerous!)"
        echo ""
        echo "Examples:"
        echo "  ./migrate.sh create \"add property table\""
        echo "  ./migrate.sh up"
        echo "  ./migrate.sh down"
        echo "  ./migrate.sh down 2"
        ;;
esac
