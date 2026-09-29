import { MongoClient } from 'mongodb';

let client;
let clientPromise;

const uri = process.env.MONGO_URI;

if (uri) {
  client = new MongoClient(uri);
  clientPromise = client.connect();
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const data = req.method === 'POST' ? req.body : req.query;
  const { email, name, phone, interest, message, source } = data || {};

  if (!email) {
    return res.status(400).json({ success: false, message: 'Email required' });
  }

  const inquiry = {
    id: Date.now().toString(),
    email: email.toLowerCase().trim(),
    name: name || 'Not provided',
    phone: phone || '',
    interest: interest || 'General',
    message: message || '',
    source: source || 'website',
    timestamp: new Date().toISOString()
  };

  try {
    if (clientPromise) {
      const client = await clientPromise;
      const db = client.db('daycare_db');
      await db.collection('enquiries').insertOne(inquiry);
    }
    return res.status(200).json({ success: true, message: 'Inquiry saved successfully' });
  } catch (err) {
    console.error('Database save error:', err);
    return res.status(200).json({ success: true, message: 'Inquiry received' });
  }
}
