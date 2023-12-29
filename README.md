This is a VERY early 'build' of my Python Halo Modules.  Right now, there are not any solid set up instructions, so you will probably need some understanding of python to get it working. Alternatively, raise an issue and I can try to help you get it set up!

I am planning on fleshing it out over the coming months, including a more user friendly interface for setup and config.



# Setting up Halo
1. Login to your Halo instance and go to HaloPSA API here: (your tenant).halopsa.com/config/integrations/api
2. Under Applications, click "View Applications"
3. Create a new application, and set type to Client ID and Secret (Service).
4. Name it something memorable, so it doesn't get deleted accidentally.
5. Set login type to Agent and seelct any agent (I use my own, but make sure whatever you pick has permissions to do the actions you will be using)
6. Make sure that "Active" is ticked and click save (Not: this shouldn't be needed, but I have lost my progress too many times to risk it)
7. Note your Client ID and Secret, you will need these later!
8. Click on the integration/Application you just created and go to Permissions.
9. Set permissions to either All or, if you know what you'll be using, enable just those permissions. (I recommend testing with All and then disabling permissions selectively, that way you know your connection is working before you start troubleshooting)
10. Click Save and move on to setting up your .env file (See example in github)

# Setting up your .env file
## Halo
1. Paste in your client ID and Secret. Do NOT put them in quotes or brackets, just paste them in after the "="
2. Replace [Your Halo Tenant] with your halo tenant name (This is the first part of the URL when you login to Halo) eg: yourcompany.halopsa.com.