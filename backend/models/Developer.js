// backend/models/Developer.js
const mongoose = require('mongoose');

// تعريف نموذج المبرمج
const developerSchema = new mongoose.Schema({
  name: { type: String, required: true },      // اسم المبرمج
  skills: [String],                             // المهارات
  bio: String,                                  // نبذة عن المبرمج
  followers: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Developer' }] // المتابعين
});

// تصدير النموذج لاستخدامه بالسيرفر
module.exports = mongoose.model('Developer', developerSchema);