const dotenv = require("dotenv")

dotenv.config({path:'../.env'});

console.log('url (1): ', process.env.SUPABASE_URL);

console.log('url (2): ', process.env.SUPABASE_URL);

console.log('url (3): ', process.env.SUPABASE_URL);

const url = process.env.SUPABASE_ROLE_SERVICE_KEY;
console.log('url (4): ', url);





console.log("URL:", process.env.SUPABASE_URL);