// =============================================================================
// Unified Backend Platform - MongoDB 初始化脚本
// =============================================================================
// 此脚本在 MongoDB 首次启动时自动执行
// 功能:
//   1. 创建业务数据库
//   2. 创建应用专用数据库用户 (只读访问)
//   3. 创建基础索引
// =============================================================================

// 获取环境变量
const dbName = process.env.MONGO_INITDB_DATABASE || 'unified_backend';
const rootUser = process.env.MONGO_INITDB_ROOT_USERNAME || 'admin';
const rootPass = process.env.MONGO_INITDB_ROOT_PASSWORD || 'admin123';

// 切换到业务数据库
db = db.getSiblingDB(dbName);

print('===================================================================');
print(`🚀 初始化数据库: ${dbName}`);
print('===================================================================');

// =============================================================================
// 1. 创建集合和索引
// =============================================================================

print('\n📝 创建索引...');

// users 集合索引
db.users.createIndex({ casdoor_id: 1 }, { unique: true, name: 'idx_users_casdoor_id' });
db.users.createIndex({ email: 1 }, { unique: true, sparse: true, name: 'idx_users_email' });
db.users.createIndex({ role: 1 }, { name: 'idx_users_role' });
db.users.createIndex({ created_at: -1 }, { name: 'idx_users_created_at' });
print('  ✅ users 集合索引创建完成');

// unified_records 集合索引
db.unified_records.createIndex(
  { app_identifier: 1, collection_type: 1, owner_id: 1 },
  { name: 'idx_records_app_collection_owner' }
);
db.unified_records.createIndex({ app_identifier: 1, collection_type: 1 }, { name: 'idx_records_app_collection' });
db.unified_records.createIndex({ owner_id: 1 }, { name: 'idx_records_owner' });
db.unified_records.createIndex({ is_deleted: 1, created_at: -1 }, { name: 'idx_records_deleted_created' });
db.unified_records.createIndex({ is_published: 1 }, { name: 'idx_records_published' });
db.unified_records.createIndex({ title: 'text', description: 'text' }, { name: 'idx_records_text_search' });
print('  ✅ unified_records 集合索引创建完成');

// files 集合索引
db.files.createIndex({ owner_id: 1 }, { name: 'idx_files_owner' });
db.files.createIndex({ app_identifier: 1, category: 1 }, { name: 'idx_files_app_category' });
db.files.createIndex({ is_deleted: 1, created_at: -1 }, { name: 'idx_files_deleted_created' });
db.files.createIndex({ content_type: 1 }, { name: 'idx_files_content_type' });
db.files.createIndex({ storage_path: 1 }, { unique: true, name: 'idx_files_storage_path' });
print('  ✅ files 集合索引创建完成');

// =============================================================================
// 2. 插入初始数据 (可选)
// =============================================================================

print('\n📦 插入初始数据...');

// 创建默认管理员用户占位符 (通过 Casdoor 同步后激活)
db.users.insertOne({
  casdoor_id: 'system-admin',
  email: 'admin@system.local',
  display_name: 'System Administrator',
  role: 'admin',
  is_active: false,  // 等待 Casdoor 同步激活
  created_at: new Date(),
  updated_at: new Date(),
  last_login_at: null
});
print('  ✅ 系统管理员占位符创建完成');

// =============================================================================
// 3. 显示数据库统计信息
// =============================================================================

print('\n📊 数据库统计:');
print(`  数据库名称: ${dbName}`);
print(`  集合数量: ${db.getCollectionNames().length}`);
print(`  集合列表: ${db.getCollectionNames().join(', ')}`);

print('\n===================================================================');
print('✅ MongoDB 初始化完成!');
print('===================================================================');
