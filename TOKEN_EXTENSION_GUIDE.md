# 🔐 FACEBOOK TOKEN EXTENSION GUIDE

## 🎯 **EXTEND YOUR TOKEN TO 60 DAYS VALIDITY**

Your current token expires today! Here's how to extend it to a long-lived token valid for 60 days.

---

## 🚀 **METHOD 1: AUTOMATIC EXTENSION (RECOMMENDED)**

### **Step 1: Run the Token Extender**
```bash
python simple_extend_token.py
```

### **Step 2: Enter Your App Credentials**
- **App ID:** Get from [Facebook Developers Console](https://developers.facebook.com/)
- **App Secret:** Get from your Facebook app settings

### **Step 3: Update Configuration**
The script will give you a new token. Update `config.py`:
```python
FACEBOOK_ACCESS_TOKEN = "YOUR_NEW_EXTENDED_TOKEN_HERE"
```

### **Step 4: Test New Token**
```bash
python simple_token_manager.py
```

---

## 🛠️ **METHOD 2: MANUAL EXTENSION**

### **Step 1: Get App Credentials**
1. Go to [Facebook Developers Console](https://developers.facebook.com/)
2. Select your app
3. Go to **Settings** → **Basic**
4. Copy **App ID** and **App Secret**

### **Step 2: Use Graph API Explorer**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click **"Generate Access Token"**
4. Select permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
   - `public_profile`
5. Click **"Generate Access Token"**
6. Copy the token

### **Step 3: Extend Token**
1. Go to [Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
2. Paste your token
3. Click **"Extend Access Token"**
4. Copy the extended token (60 days validity)

### **Step 4: Get Page Token**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Use the extended token
3. Make request to: `/{your_page_id}?fields=access_token`
4. Copy the page access token

---

## 🔍 **METHOD 3: USING FACEBOOK TOOLS**

### **Step 1: Facebook Token Debugger**
1. Go to [Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
2. Paste your current token
3. Click **"Extend Access Token"**
4. Copy the extended token

### **Step 2: Get Page Access Token**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Use the extended token
3. Make request to: `/{your_page_id}?fields=access_token`
4. Copy the page access token

---

## 📊 **TOKEN TYPES EXPLAINED**

### **Short-Lived Token (1-2 hours)**
- **Validity:** 1-2 hours
- **Use:** Initial authentication
- **Extension:** Can be extended to long-lived

### **Long-Lived Token (60 days)**
- **Validity:** 60 days
- **Use:** Production automation
- **Extension:** Can be refreshed before expiry

### **Page Access Token (60 days)**
- **Validity:** 60 days
- **Use:** Posting to Facebook pages
- **Extension:** Best for automation systems

---

## 🎯 **RECOMMENDED WORKFLOW**

### **For Immediate Fix:**
1. **Run:** `python simple_extend_token.py`
2. **Enter:** Your Facebook App ID and Secret
3. **Copy:** The new extended token
4. **Update:** `config.py` with new token
5. **Test:** `python simple_token_manager.py`

### **For Long-Term Automation:**
1. **Set up:** Automatic token monitoring
2. **Use:** Token-managed automation system
3. **Monitor:** Token health daily
4. **Refresh:** Before expiry (every 60 days)

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

**1. "App ID and Secret are required"**
- **Solution:** Get credentials from Facebook Developers Console
- **Location:** Settings → Basic → App ID and App Secret

**2. "Token extension failed"**
- **Solution:** Check if your app has the required permissions
- **Required:** `pages_manage_posts`, `pages_read_engagement`

**3. "Page access token failed"**
- **Solution:** Ensure your page is added to your Facebook app
- **Check:** App → Products → Pages → Add Page

**4. "Token validation failed"**
- **Solution:** Check if the token has the correct permissions
- **Test:** Use Graph API Explorer to verify

---

## 📈 **BENEFITS OF EXTENDED TOKEN**

### **For Your Automation:**
- ✅ **60 days validity** instead of 1-2 hours
- ✅ **No daily token updates** needed
- ✅ **Stable automation** for 2 months
- ✅ **Reduced manual intervention**
- ✅ **Professional operation**

### **For Reliability:**
- ✅ **Long-term stability** for automation
- ✅ **Reduced token management** overhead
- ✅ **Better for production** systems
- ✅ **Less frequent updates** required

---

## 🚀 **AFTER EXTENSION**

### **Update Your System:**
1. **Update config.py** with new token
2. **Test token** with `python simple_token_manager.py`
3. **Restart automation** with `python monetization_optimized_schedule.py`
4. **Monitor token health** regularly

### **Set Up Monitoring:**
1. **Check token status** weekly
2. **Set calendar reminder** for 50 days
3. **Prepare for next refresh** before expiry
4. **Document the process** for future use

---

## 🎉 **SUCCESS INDICATORS**

### **Token Extension Successful When:**
- ✅ **New token obtained** (60 days validity)
- ✅ **Page access token** working
- ✅ **Token validation** passes
- ✅ **Automation system** continues working
- ✅ **No manual intervention** needed for 60 days

### **Your System Now Has:**
- 🔐 **Long-lived token** (60 days)
- 🚀 **Stable automation** without interruption
- 📊 **Reduced maintenance** overhead
- 🎯 **Professional operation** for 2 months

---

## 🚨 **CRITICAL REMINDER**

**Your current token expires TODAY!**

**Follow the steps above to extend your token immediately.**

**Your automation system will stop working without a valid token!**

**Use Method 1 (Automatic Extension) for the fastest solution!** 🚀


