# 🔐 FACEBOOK TOKEN EXTENSION - MANUAL STEPS

## 🚨 **URGENT: YOUR TOKEN EXPIRES TODAY!**

Your current Facebook token expires in **0 days**. Follow these steps to extend it to 60 days validity.

---

## 🚀 **STEP-BY-STEP EXTENSION PROCESS**

### **Step 1: Get Your Facebook App Credentials**
1. Go to [Facebook Developers Console](https://developers.facebook.com/)
2. Select your app
3. Go to **Settings** → **Basic**
4. Copy your **App ID** and **App Secret**

### **Step 2: Use Facebook Graph API Explorer**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click **"Generate Access Token"**
4. Select these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
   - `public_profile`
5. Click **"Generate Access Token"**
6. Copy the generated token

### **Step 3: Extend Token to Long-Lived**
1. Go to [Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
2. Paste your token from Step 2
3. Click **"Extend Access Token"**
4. Copy the extended token (this will be valid for 60 days)

### **Step 4: Get Page Access Token**
1. Go back to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Use the extended token from Step 3
3. Make a request to: `/{your_page_id}?fields=access_token`
   - Replace `{your_page_id}` with `758737463999000`
   - So the request is: `/758737463999000?fields=access_token`
4. Copy the `access_token` value from the response

### **Step 5: Update Your Configuration**
1. Open `config.py`
2. Replace the current token with the new one:
```python
FACEBOOK_ACCESS_TOKEN = "YOUR_NEW_EXTENDED_TOKEN_HERE"
```

### **Step 6: Test the New Token**
```bash
python simple_token_manager.py
```

---

## 🔍 **DETAILED INSTRUCTIONS**

### **For Step 2 (Graph API Explorer):**
1. **URL:** https://developers.facebook.com/tools/explorer/
2. **App:** Select your app from dropdown
3. **Permissions:** Click "Get Token" → "Get User Access Token"
4. **Select:** All the permissions listed above
5. **Generate:** Click "Generate Access Token"
6. **Copy:** The token that appears

### **For Step 3 (Token Debugger):**
1. **URL:** https://developers.facebook.com/tools/debug/accesstoken/
2. **Paste:** Your token from Step 2
3. **Extend:** Click "Extend Access Token" button
4. **Copy:** The extended token (60 days validity)

### **For Step 4 (Page Access Token):**
1. **URL:** https://developers.facebook.com/tools/explorer/
2. **Token:** Use the extended token from Step 3
3. **Request:** `GET /758737463999000?fields=access_token`
4. **Response:** Look for `"access_token": "YOUR_PAGE_TOKEN"`
5. **Copy:** The page access token value

---

## 📊 **EXPECTED RESULTS**

### **After Step 3 (Extended Token):**
- **Validity:** 60 days
- **Type:** Long-lived user token
- **Use:** For getting page access token

### **After Step 4 (Page Access Token):**
- **Validity:** 60 days
- **Type:** Page access token
- **Use:** For posting to your Facebook page

### **After Step 6 (Testing):**
- **Status:** Token valid
- **Page:** "The Unseen Economy"
- **Expiry:** 60 days from now
- **Ready:** For automation

---

## 🚨 **CRITICAL TIMELINE**

### **Today (Immediate):**
- ✅ **Step 1-4:** Get new extended token
- ✅ **Step 5:** Update config.py
- ✅ **Step 6:** Test new token

### **This Week:**
- ✅ **Monitor:** Token health daily
- ✅ **Test:** Automation system
- ✅ **Document:** Process for future

### **Next 60 Days:**
- ✅ **Automation:** Runs without interruption
- ✅ **Monitoring:** Check token health weekly
- ✅ **Preparation:** Set reminder for next refresh

---

## 🔧 **TROUBLESHOOTING**

### **If Step 2 Fails:**
- **Check:** Your app has the required permissions
- **Verify:** You're logged into the correct Facebook account
- **Try:** Generating token again

### **If Step 3 Fails:**
- **Check:** The token is valid and not expired
- **Verify:** Your app has the correct settings
- **Try:** Using a different browser

### **If Step 4 Fails:**
- **Check:** The extended token is valid
- **Verify:** Your page ID is correct (758737463999000)
- **Try:** Making the request again

### **If Step 6 Fails:**
- **Check:** The token is correctly copied
- **Verify:** No extra spaces or characters
- **Try:** Testing with Graph API Explorer first

---

## 🎯 **SUCCESS CHECKLIST**

### **Before Starting:**
- [ ] Facebook Developers Console access
- [ ] App ID and Secret available
- [ ] Page ID: 758737463999000
- [ ] Current token expires today

### **After Completion:**
- [ ] New token obtained (60 days)
- [ ] Page access token working
- [ ] config.py updated
- [ ] Token validation passes
- [ ] Automation system ready

---

## 🚀 **NEXT STEPS AFTER EXTENSION**

### **Immediate Actions:**
1. **Update config.py** with new token
2. **Test token** with `python simple_token_manager.py`
3. **Restart automation** with `python monetization_optimized_schedule.py`
4. **Verify posting** works correctly

### **Long-Term Setup:**
1. **Set calendar reminder** for 50 days from now
2. **Document the process** for future use
3. **Monitor token health** weekly
4. **Prepare for next refresh** before expiry

---

## 🎉 **BENEFITS OF EXTENDED TOKEN**

### **For Your Automation:**
- ✅ **60 days validity** instead of 1-2 hours
- ✅ **No daily updates** needed
- ✅ **Stable automation** for 2 months
- ✅ **Professional operation**
- ✅ **Reduced maintenance**

### **For Your Business:**
- ✅ **Uninterrupted posting** for 60 days
- ✅ **Maximum USA reach** maintained
- ✅ **Monetization optimization** continues
- ✅ **Professional automation** without breaks

---

## 🚨 **CRITICAL REMINDER**

**Your current token expires TODAY!**

**Follow these steps immediately to prevent automation failure.**

**Your system will stop working without a valid token!**

**Start with Step 1 now!** 🚀


