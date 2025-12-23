// MongoDB User Initialization Script
// This script is executed on first container start

// Switch to admin database
db = db.getSiblingDB('admin');

// Create root user (only if doesn't exist)
try {
    db.createUser({
        user: 'admin',
        pwd: 'admin123',
        roles: [
            { role: 'root', db: 'admin' }
        ]
    });
    print('✅ Root user "admin" created successfully');
} catch (e) {
    if (e.code === 51003) {
        print('ℹ️ Root user "admin" already exists');
    } else {
        print('❌ Error creating root user:', e);
    }
}

// Create application database user
db = db.getSiblingDB('unified_backend');
try {
    db.createUser({
        user: 'app_user',
        pwd: 'app_pass123',
        roles: [
            { role: 'readWrite', db: 'unified_backend' }
        ]
    });
    print('✅ Application user "app_user" created successfully');
} catch (e) {
    if (e.code === 51003) {
        print('ℹ️ Application user "app_user" already exists');
    } else {
        print('❌ Error creating app user:', e);
    }
}

print('🎉 MongoDB initialization completed!');
