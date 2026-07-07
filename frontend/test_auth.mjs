import fs from 'fs';
import { createClient } from '@supabase/supabase-js';

// Parse .env.local
const envContent = fs.readFileSync('.env.local', 'utf-8');
envContent.split('\n').forEach(line => {
    const match = line.match(/^([^=]+)=(.*)$/);
    if (match) {
        process.env[match[1].trim()] = match[2].trim();
    }
});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("Missing Supabase credentials in .env.local!");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function testAuth() {
    console.log(`Connecting to: ${supabaseUrl}`);
    console.log("-----------------------------------------");
    
    console.log("Attempting sign in with WRONG password...");
    const badLogin = await supabase.auth.signInWithPassword({
        email: 'test-real-auth@example.com',
        password: 'wrong_password_123!'
    });
    
    if (badLogin.error) {
        console.log("✅ Success! Supabase correctly REJECTED the wrong password:");
        console.log(`   Error: ${badLogin.error.message}`);
    } else {
        console.log("❌ Failed! Supabase accepted the wrong password.");
    }
    
    console.log("-----------------------------------------");
    console.log("Attempting to sign up a new test user...");
    const signUp = await supabase.auth.signUp({
        email: `test-user-${Date.now()}@example.com`,
        password: 'ValidPassword123!'
    });
    
    if (signUp.error) {
        console.log(`❌ Sign up failed: ${signUp.error.message}`);
    } else {
        console.log("✅ Success! Real user created in Supabase Auth.");
        console.log(`   User ID: ${signUp.data.user?.id}`);
        console.log(`   Returned JWT length: ${signUp.data.session?.access_token.length} chars`);
    }
}

testAuth();
