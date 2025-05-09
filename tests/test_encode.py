import pytest
from encode import encode_decode, handle_encode_decode_command

def test_encode_decode_base64():
    text = "hello world"
    encoded = encode_decode(text, "base64", "encode")
    decoded = encode_decode(encoded, "base64", "decode")
    assert decoded == text

def test_encode_decode_binary():
    text = "hello world"
    encoded = encode_decode(text, "binary", "encode")
    decoded = encode_decode(encoded, "binary", "decode")
    assert decoded == text

def test_encode_decode_rot13():
    text = "hello world"
    encoded = encode_decode(text, "rot13", "encode")
    decoded = encode_decode(encoded, "rot13", "decode")
    assert decoded == text

def test_encode_decode_morse():
    text = "helloworld"
    encoded = encode_decode(text, "morse", "encode")
    decoded = encode_decode(encoded, "morse", "decode")
    assert decoded.upper() == text.upper()

def test_handle_encode_decode_command():
    args = ["base64", "hello world"]
    result = handle_encode_decode_command(args, "encode")
    assert "Encoded Text" in result

    args = ["binary", "hello world"]
    result = handle_encode_decode_command(args, "encode")
    assert "Encoded Text" in result

    args = ["rot13", "hello world"]
    result = handle_encode_decode_command(args, "encode")
    assert "Encoded Text" in result

    args = ["morse", "hello world"]
    result = handle_encode_decode_command(args, "encode")
    assert "Encoded Text" in result

def test_handle_decode_command():
    args = ["base64", "aGVsbG8="]
    result = handle_encode_decode_command(args, "decode")
    assert "Decoded Text" in result

    args = ["binary", "01101000 01100101 01101100 01101100 01101111"]
    result = handle_encode_decode_command(args, "decode")
    assert "Decoded Text" in result

    args = ["rot13", "uryyb"]
    result = handle_encode_decode_command(args, "decode")
    assert "Decoded Text" in result

    args = ["morse", ".... . .-.. .-.. ---"]
    result = handle_encode_decode_command(args, "decode")
    assert "Decoded Text" in result

def test_handle_invalid_encode_command():
    args = ["invalid", "hello"]
    with pytest.raises(ValueError, match="Unknown method: invalid. Available methods are: binary, base64, rot13, morse, all"):
        handle_encode_decode_command(args, "encode")

def test_handle_invalid_decode_command():
    args = ["invalid", "hello"]
    with pytest.raises(ValueError, match="Unknown method: invalid. Available methods are: binary, base64, rot13, morse, all"):
        handle_encode_decode_command(args, "decode")

def test_handle_decode_with_invalid_data():
    args = ["base64", "invalid_binary"]
    result = handle_encode_decode_command(args, "decode")
    assert "Invalid input `invalid_binary` provided to `base64` decode, please provide valid input." in result