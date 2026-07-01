FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     git curl wget cmake pkg-config build-essential \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/contrasted

RUN git clone https://github.com/dmmiller597/contrasted .

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
RUN uv sync

ENV HF_HOME=/opt/huggingface
ENV PATH="/opt/contrasted/.venv/bin:$PATH"

CMD ["/bin/bash"]
# Optional: bake ProstT5 weights into the image. This will make the image much larger (already 19G).
# RUN uv run python -c "from transformers import T5EncoderModel, T5Tokenizer; T5Tokenizer.from_pretrained('Rostlab/ProstT5'); T5EncoderModel.from_pretrained('Rostlab/ProstT5')"