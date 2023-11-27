/*
 Navicat Premium Data Transfer

 Source Server         : CS50P
 Source Server Type    : SQLite
 Source Server Version : 3035005 (3.35.5)
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3035005 (3.35.5)
 File Encoding         : 65001

 Date: 27/11/2023 09:14:23
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS "categories";
CREATE TABLE "categories" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "name" TEXT NOT NULL,
  "created_at" TEXT NOT NULL,
  "status" INTEGER DEFAULT 1,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for preferences
-- ----------------------------
DROP TABLE IF EXISTS "preferences";
CREATE TABLE "preferences" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "key" TEXT,
  "value" TEXT,
  "created_at" TEXT,
  "status" INTEGER DEFAULT 1,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION,
  UNIQUE ("key" ASC)
);

-- ----------------------------
-- Table structure for priorities
-- ----------------------------
DROP TABLE IF EXISTS "priorities";
CREATE TABLE "priorities" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "name" TEXT NOT NULL,
  "color" TEXT NOT NULL,
  "created_at" TEXT NOT NULL,
  "status" INTEGER DEFAULT 1,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for sqlite_sequence
-- ----------------------------
DROP TABLE IF EXISTS "sqlite_sequence";
CREATE TABLE "sqlite_sequence" (
  "name",
  "seq"
);

-- ----------------------------
-- Table structure for tasks
-- ----------------------------
DROP TABLE IF EXISTS "tasks";
CREATE TABLE "tasks" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "name" TEXT NOT NULL,
  "due_date" TEXT,
  "priority" TEXT,
  "category" TEXT,
  "created_at" TEXT,
  "status" INTEGER,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for user_activity
-- ----------------------------
DROP TABLE IF EXISTS "user_activity";
CREATE TABLE "user_activity" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "type" TEXT NOT NULL,
  "created_at" TEXT NOT NULL,
  "status" TEXT,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION
);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "users";
CREATE TABLE "users" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "username" TEXT NOT NULL,
  "email" TEXT,
  "password" TEXT NOT NULL,
  "salt" TEXT NOT NULL,
  "created_at" TEXT NOT NULL,
  "status" INTEGER DEFAULT 1
);

-- ----------------------------
-- Auto increment value for users
-- ----------------------------
UPDATE "sqlite_sequence" SET seq = 1 WHERE name = 'users';

PRAGMA foreign_keys = true;
