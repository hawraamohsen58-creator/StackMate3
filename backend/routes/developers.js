const express = require('express');
const router = express.Router();
const Developer = require('../models/Developer');

// جلب المطورين مع البحث
router.get('/', async (req, res) => {
  const { search } = req.query;
  try {
    const query = search
      ? { name: { $regex: search, $options: 'i' } }
      : {};
    const developers = await Developer.find(query);
    res.json(developers);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// إضافة متابع (Follow)
router.post('/follow/:id', async (req, res) => {
  const { id } = req.params; // المبرمج اللي رح نتابعه
  const { followerId } = req.body; // مين يتابع
  try {
    const dev = await Developer.findById(id);
    if (!dev) return res.status(404).json({ message: 'Developer not found' });

    // إذا المتابع موجود مسبقاً، لا تضيفه مرتين
    if (!dev.followers.includes(followerId)) {
      dev.followers.push(followerId);
      await dev.save();
    }

    res.json({ message: 'Followed successfully', developer: dev });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;