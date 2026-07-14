.PHONY: server client

server:
	python agent_server/start_server.py

client:
	python client/client.py
