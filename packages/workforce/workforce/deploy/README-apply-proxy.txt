Apply proxy config and run uvicorn (step-by-step)

1) Place the config
   - Copy deploy/openresty-proxy.conf -> /etc/nginx/sites-available/workforce
   - sudo ln -s /etc/nginx/sites-available/workforce /etc/nginx/sites-enabled/

2) Choose socket or TCP upstream
   - Recommended (unix socket): configure uvicorn to listen on /run/workforce.sock
     ExecStart example in systemd below uses --uds /run/workforce.sock
   - Alternative: run uvicorn on 127.0.0.1:8001 and use the TCP upstream in the nginx file

3) Example systemd service (save as /etc/systemd/system/workforce.service):

[Unit]
Description=Uvicorn instance for Workforce
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/hn3t/scheduler/workforce
Environment=PATH=/home/hn3t/scheduler/workforce/venv/bin
ExecStart=/home/hn3t/scheduler/workforce/venv/bin/uvicorn app.main:app --uds /run/workforce.sock --log-level info
Restart=always

[Install]
WantedBy=multi-user.target

Notes:
 - Ensure the socket path (/run/workforce.sock) is writable by the proxy user (usually www-data/nginx).
 - If you use a unix socket, remove the TCP proxy_pass and enable the unix proxy_pass line.
 - If your proxy performs TLS termination (recommended), keep TLS at the proxy and proxy_pass over HTTP/uDS.

4) Reload systemd and start the service
   sudo systemctl daemon-reload
   sudo systemctl enable --now workforce.service

5) Test the socket or TCP upstream
   - For TCP: curl -i -H "Content-Type: application/json" -X POST -d '{"email":"demo-owner@workforce.app","password":"DemoOwner2026!"}' http://127.0.0.1:8001/api/v1/auth/login
   - For unix socket: curl -i --unix-socket /run/workforce.sock -H "Content-Type: application/json" -X POST -d '{"email":"demo-owner@workforce.app","password":"DemoOwner2026!"}' http://localhost/api/v1/auth/login

6) Check Nginx/OpenResty config and reload
   sudo nginx -t
   sudo systemctl reload nginx    # or: sudo systemctl reload openresty

7) Verify public request returns JSON (no HTML error)
   curl -i -H "Content-Type: application/json" -X POST -d '{"email":"demo-owner@workforce.app","password":"DemoOwner2026!"}' https://your-public-hostname/api/v1/auth/login

Troubleshooting:
 - If you see HTML errors from OpenResty, look for auth directives (auth_basic / auth_basic_user_file) in nginx config and remove them for API endpoints.
 - If using SELinux, ensure nginx can access the socket (setsebool or configure accordingly).
 - Ensure firewall allows the proxy to accept public traffic (port 80/443) but the upstream socket/port is local-only.
