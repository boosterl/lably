from dymo_bluetooth import discover_printers, create_image, create_code_128
import asyncio

class PrinterException(Exception):
    pass

def print_image(input_file, reverse=False):
    print(f"Printing file: {input_file}")
    print(f"Reverse: {reverse}")
    initial_canvas = create_image(input_file)
    return asyncio.run(print_image_async(initial_canvas, reverse))

def print_barcode(text, reverse=False):
    print(f"Reverse: {reverse}")
    print(f"Printing text: {text}")
    initial_canvas = create_code_128(text)
    return asyncio.run(print_image_async(initial_canvas, reverse))

async def print_image_async(canvas, reverse):
    canvas = canvas.stretch(factor=2)
    if reverse:
        canvas = canvas.revert()
    printers = await discover_printers(5)
    if not printers:
        raise PrinterException("Couldn't find any printers")
    printer = printers[0]
    await printer.connect()
    await printer.print(canvas)
