from flask import Flask, jsonify

app = Flask(__name__)

# ハードコードされた秘密鍵（脆弱性）
app.config['SECRET_KEY'] = 'my-super-secret-key-that-is-not-safe'

@app.route('/')
def hello():
    return "Hello, World! This is a sample vulnerable app."

@app.route('/api/data')
def get_data():
    return jsonify({"data": "some sensitive data"})

if __name__ == '__main__':
    # デバッグモードでの実行も潜在的な脆弱性です
    app.run(host='0.0.0.0', port=5000, debug=True)
