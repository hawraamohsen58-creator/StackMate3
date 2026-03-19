// backend/server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const Developer = require('./models/Developer');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// ===============================
// اتصال MongoDB Atlas
// ===============================
mongoose.connect('mongodb+srv://hawraawaleed33_db_user:VyTQdtnppS9lT0RK@cluster0.jeyjiot.mongodb.net/developers_db?retryWrites=true&w=majority')
  .then(() => console.log('MongoDB Atlas Connected ✅'))
  .catch(err => console.error('MongoDB connection error ❌', err));

// ===============================
// Developers APIs
// ===============================

// إضافة مبرمج
app.post('/developers', async (req, res) => {
  const { name, skill, bio, avatar, job, location, experience, technologies, portfolio } = req.body;
  try {
    const newDev = new Developer({
      name, skill, bio, avatar, job, location, experience, technologies, portfolio, followers: []
    });
    const savedDev = await newDev.save();
    res.status(201).json(savedDev);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});

// جلب جميع المبرمجين
app.get('/developers', async (req, res) => {
  try {
    const devs = await Developer.find();
    res.json(devs);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// جلب مبرمج بالـ ID (لصفحة الملف الشخصي)
app.get('/developers/:id', async (req, res) => {
  try {
    const dev = await Developer.findById(req.params.id);
    if (!dev) return res.status(404).json({ message: "Developer not found" });
    res.json(dev);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// البحث عن مبرمج بالاسم أو المهارة
app.get('/developers/search', async (req, res) => {
  const q = req.query.q || '';
  try {
    const devs = await Developer.find({
      $or: [
        { name: { $regex: q, $options: "i" } },
        { skill: { $regex: q, $options: "i" } }
      ]
    });
    res.json(devs);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// ===============================
// Follow API
// ===============================

// متابعة مبرمج
app.post('/follow', async (req, res) => {
  const { follower, following } = req.body;
  try {
    const dev = await Developer.findById(following);
    if (!dev) return res.status(404).json({ message: "Developer not found" });

    if (!dev.followers.includes(follower)) {
      dev.followers.push(follower);
      await dev.save();
    }

    res.json({
      message: "Follow request sent",
      followers_count: dev.followers.length
    });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// جلب جميع المتابعات (اختياري)
app.get('/follow', async (req, res) => {
  try {
    const devs = await Developer.find();
    const result = devs.map(d => ({
      id: d._id,
      name: d.name,
      followers_count: d.followers.length
    }));
    res.json(result);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// صفحة اختبار السيرفر
app.get('/', (req, res) => {
  res.send('Server is running ✅');
});

// ===============================
// إعدادات Render Deployment
// ===============================
const PORT = process.env.PORT || 8001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT} 🚀`);
});