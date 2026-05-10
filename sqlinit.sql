-- 删除已存在的数据库（注意：会删除所有数据，请谨慎！）
DROP DATABASE IF EXISTS c2_coordinator;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS c2_coordinator DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE c2_coordinator;

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入默认admin用户（请将'请替换为实际bcrypt哈希'替换为真实的bcrypt加密后的密码）
INSERT INTO `users` (`username`, `password_hash`) VALUES ('admin', '请替换为实际bcrypt哈希');

-- MSF会话缓存表
CREATE TABLE IF NOT EXISTS `msf_sessions` (
  `id` VARCHAR(64) NOT NULL,
  `host` VARCHAR(255),
  `user` VARCHAR(255),
  `platform` VARCHAR(50),
  `created_at` DATETIME,
  `last_seen` DATETIME,
  `status` VARCHAR(20) DEFAULT 'active',
  `synced_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE INDEX idx_msf_status ON `msf_sessions` (`status`);

-- Sliver会话缓存表
CREATE TABLE IF NOT EXISTS `sliver_sessions` (
  `id` VARCHAR(64) NOT NULL,
  `host` VARCHAR(255),
  `user` VARCHAR(255),
  `platform` VARCHAR(50),
  `created_at` DATETIME,
  `last_seen` DATETIME,
  `status` VARCHAR(20) DEFAULT 'active',
  `synced_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE INDEX idx_sliver_status ON `sliver_sessions` (`status`);

-- 会话映射表
CREATE TABLE IF NOT EXISTS `session_mappings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `msf_session_id` VARCHAR(64) NOT NULL,
  `sliver_session_id` VARCHAR(64) NOT NULL,
  `implanted_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `status` VARCHAR(20) DEFAULT 'active',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`msf_session_id`) REFERENCES `msf_sessions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`sliver_session_id`) REFERENCES `sliver_sessions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE INDEX idx_mapping_status ON `session_mappings` (`status`);

-- 操作日志表
CREATE TABLE IF NOT EXISTS `operation_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `action` VARCHAR(50) NOT NULL,
  `target` VARCHAR(255),
  `result` VARCHAR(20),
  `detail` TEXT,
  `ip_address` VARCHAR(45),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE INDEX idx_logs_user_id ON `operation_logs` (`user_id`);
CREATE INDEX idx_logs_created_at ON `operation_logs` (`created_at`);
CREATE INDEX idx_logs_action ON `operation_logs` (`action`);

-- IP池表
CREATE TABLE IF NOT EXISTS `ip_pool` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `ip_address` VARCHAR(45) NOT NULL UNIQUE,
  `enabled` TINYINT(1) DEFAULT 1,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 域名动态解析配置表（单行） 修正版
CREATE TABLE IF NOT EXISTS `domain_dns_config` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `domain` VARCHAR(255) NOT NULL,
  `current_ip` VARCHAR(45),
  `update_interval` INT DEFAULT 60,
  `enabled` TINYINT(1) DEFAULT 0,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 流量混淆配置表（单行）
CREATE TABLE IF NOT EXISTS `traffic_obfuscation_config` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `encryption` VARCHAR(20) DEFAULT 'AES-256',
  `random_headers` TINYINT(1) DEFAULT 1,
  `data_chunking` TINYINT(1) DEFAULT 1,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;