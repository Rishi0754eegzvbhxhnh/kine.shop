const fs = require('fs');
const { MongoClient } = require('mongodb');

async function seed() {
    const url = process.env.MONGO_URL || 'mongodb://shoppable_mongo:27017';
    const client = new MongoClient(url);

    try {
        await client.connect();
        console.log("Connected to MongoDB.");
        const db = client.db('shoppablestream');
        const collection = db.collection('videoMetadata');

        const timelineRaw = fs.readFileSync('./frontend/public/sam3_charade_timeline.json', 'utf-8');
        const timeline = JSON.parse(timelineRaw);

        const doc1 = {
            filename: '/Charade_1963.mp4',
            status: 'completed',
            timeline: timeline
        };
        const doc2 = {
            filename: '/Charade_1963_short.mp4',
            status: 'completed',
            timeline: timeline
        };

        await collection.deleteMany({ filename: { $in: ['/Charade_1963.mp4', '/Charade_1963_short.mp4', 'Charade_1963.mp4', 'Charade_1963_short.mp4'] } });
        
        await collection.insertOne({ ...doc1, filename: 'Charade_1963.mp4' });
        await collection.insertOne({ ...doc2, filename: 'Charade_1963_short.mp4' });
        await collection.insertOne(doc1);
        await collection.insertOne(doc2);

        console.log("Successfully seeded dummy video metadata!");
    } catch (err) {
        console.error(err);
    } finally {
        await client.close();
    }
}

seed();
