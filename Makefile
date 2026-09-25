.PHONY: server client ping

ping:
	python scripts/lakebase_ping.py

server: ping
	python agent_server/start_server.py

client:
	python client/client.py
