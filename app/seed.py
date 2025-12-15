import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.repositories.admin_repo import AdminRepository
from app.repositories.user_repo import UserRepository
from app.repositories.settings_repo import SettingsRepository


async def seed_data():
    """Seed admin and sample users if they don't exist."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Seed Admin
        admin_repo = AdminRepository(session)
        admin = await admin_repo.get_by_username("admin", include_deleted=False)
        
        if not admin:
            hashed_password = hash_password("admin123")
            admin = await admin_repo.create_admin(
                username="admin",
                name="Admin User",
                email="admin@example.com",
                hashed_password=hashed_password,
                is_active=True
            )
            print(f"[OK] Admin created: {admin.username} (ID: {admin.id})")
            print(f"     Email: {admin.email}")
            print(f"     Password: admin123")
        else:
            print(f"[OK] Admin already exists: {admin.username}")

        # Seed Sample User
        user_repo = UserRepository(session)
        user = await user_repo.get_by_username("testuser", include_deleted=False)
        
        if not user:
            hashed_password = hash_password("user123")
            user = await user_repo.create_user(
                username="testuser",
                name="Test User",
                email="user@example.com",
                hashed_password=hashed_password
            )
            print(f"[OK] User created: {user.username} (ID: {user.id})")
            print(f"     Email: {user.email}")
            print(f"     Password: user123")
        else:
            print(f"[OK] User already exists: {user.username}")

        # Seed Default Settings
        settings_repo = SettingsRepository(session)
        
        default_settings = {
            "app_name": ("FastAPI Production Scaffold", "Application name"),
            "email": ("admin@example.com", "Application contact email"),
            "contact_info": ("Contact us at admin@example.com", "Application contact information"),
            "url": ("http://localhost:8000", "Application URL"),
        }
        
        for key, (value, description) in default_settings.items():
            existing = await settings_repo.get_setting(key)
            if not existing:
                await settings_repo.set_setting(
                    key=key,
                    value=value,
                    description=description,
                    is_public=True
                )
                print(f"[OK] Setting created: {key} = {value}")
            else:
                print(f"[OK] Setting already exists: {key}")
        
        # Note: Logo is not seeded as it requires an image file upload

        print("\n" + "="*50)
        print("SEEDING COMPLETE")
        print("="*50)
        print("\nAdmin Credentials:")
        print("  Username: admin")
        print("  Email: admin@example.com")
        print("  Password: admin123")
        print("\nUser Credentials:")
        print("  Username: testuser")
        print("  Email: user@example.com")
        print("  Password: user123")
        print("\nDefault Settings:")
        print("  app_name: FastAPI Production Scaffold")
        print("  email: admin@example.com")
        print("  contact_info: Contact us at admin@example.com")
        print("  url: http://localhost:8000")
        print("\nWARNING: Please change default passwords in production!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())