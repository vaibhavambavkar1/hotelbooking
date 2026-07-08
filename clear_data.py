from django.apps import apps
from django.contrib.auth import get_user_model

def clear_database():
    User = get_user_model()
    
    # Built-in apps that we want to preserve to keep the system running smoothly
    # (keeps permissions, admin logs, content types, and sessions intact)
    PROTECTED_APPS = ['auth', 'contenttypes', 'sessions', 'admin']
    
    print("Starting database cleanup...")
    
    # We must be careful with foreign key constraints. 
    # Deleting models in a certain order might be necessary, but Django's .delete()
    # handles cascading deletes automatically in most cases.
    
    deleted_counts = {}
    
    for model in apps.get_models():
        app_label = model._meta.app_label
        
        # 1. Skip protected built-in apps
        if app_label in PROTECTED_APPS:
            continue
            
        # 2. Skip the User model explicitly (if it's a custom user model in another app)
        if model == User:
            print(f"Skipping {model.__name__} (User model)")
            continue
            
        print(f"Deleting data from {app_label}.{model.__name__}...")
        
        try:
            # Delete all records for this model
            count, _ = model.objects.all().delete()
            if count > 0:
                deleted_counts[model.__name__] = count
        except Exception as e:
            print(f"Error deleting {model.__name__}: {str(e)}")
            
    print("\n--- Cleanup Summary ---")
    if deleted_counts:
        for model_name, count in deleted_counts.items():
            print(f"{model_name}: Deleted {count} records")
    else:
        print("No records found to delete.")
        
    print("Database cleanup finished successfully!")

if __name__ == '__main__':
    clear_database()
