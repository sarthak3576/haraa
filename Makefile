# Invoked by `sam build` (via Metadata: BuildMethod: makefile on each
# function/layer in infra/template.yaml, whose CodeUri is `../` i.e. this
# repo root). Cross-platform `pip install` -- no Docker required; see
# docs/ARCHITECTURE.md for why this is safe for every dependency here.
#
# Each target must populate $(ARTIFACTS_DIR) (set by SAM) with exactly
# what that function/layer needs -- never the whole repo, so ml/, .venv/,
# datasets, and model caches never reach the deployment package.

PY_VERSION := 3.12
PLATFORM := manylinux2014_x86_64
COMMON := bash infra/build_scripts/copy_common.sh

build-WebDepsLayer:
	/usr/bin/python3 -m pip install -r requirements-lambda.txt \
	  --platform $(PLATFORM) --implementation cp --python-version $(PY_VERSION) \
	  --only-binary=:all: --target "$(ARTIFACTS_DIR)/python"

build-WebFunction:
	mkdir -p "$(ARTIFACTS_DIR)/app"
	rsync -a \
	  --exclude='__pycache__' --exclude='*.pyc' \
	  --exclude='ml_model/*.pt' --exclude='ml_model/*.png' \
	  app/ "$(ARTIFACTS_DIR)/app/"

build-ClassifyFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp app/services/rekognition_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp infra/handlers/classify/handler.py "$(ARTIFACTS_DIR)/handler.py"

build-PresignFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp infra/handlers/presign_upload/handler.py "$(ARTIFACTS_DIR)/handler.py"

build-LogWasteFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp app/services/dashboard_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp infra/handlers/log_waste/handler.py "$(ARTIFACTS_DIR)/handler.py"

build-DashboardFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp app/services/dashboard_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/gamification_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp infra/handlers/dashboard/handler.py "$(ARTIFACTS_DIR)/handler.py"

build-QuizScoresFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp app/services/segregation_game_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp infra/handlers/quiz_scores/handler.py "$(ARTIFACTS_DIR)/handler.py"

build-ChatbotFunction:
	$(COMMON) "$(ARTIFACTS_DIR)"
	cp app/services/chatbot_service.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/chat_diagnostics.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/chat_system_prompt.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/fallback_chatbot.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/gemini_chatbot.py "$(ARTIFACTS_DIR)/app/services/"
	cp app/services/waste_items_data.py "$(ARTIFACTS_DIR)/app/services/"
	cp infra/handlers/chatbot/handler.py "$(ARTIFACTS_DIR)/handler.py"

.PHONY: build-WebDepsLayer build-WebFunction build-ClassifyFunction build-PresignFunction build-LogWasteFunction build-DashboardFunction build-QuizScoresFunction build-ChatbotFunction
