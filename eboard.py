import chess.pgn
import chess.polyglot
import serial
import time

ser = serial.Serial('COM13', baudrate=9600)
akhir = b'\xfe'
book = chess.polyglot.open_reader("opening/performance.bin")
board = chess.Board()
print(board.ply())
print(board)
engine = chess.engine.SimpleEngine.popen_uci("c:\Program Files (x86)\Tarrasch\Engines\stockfish_8_x64")
pilih = {"Skill Level": 2}
engine.configure(pilih)
play_game = True
command = 1
select_new_game = True
last_move = [129, 64, 64, 64, 64, 256]
ntransmit = 0
max_transmit = 3
ndelay = 5
delay = ndelay
client_white =  True
host_white = False
device_err = False
iter = 0
client_req = 0
client_prev_from = 0
cleint_prev_to = 0
client_from = 0
client_to = 0

def to_eboard(petak):
  file = petak & 7
  rank = petak & 56
  rank = 56 - rank
  square = rank + file
  return square

#command
#0 - 63 move from, move to
#64 - no move
#65 - normal move
#66 - move promotion to queen
#67 - move promotion to rook
#68 - move promotion to bishop
#69 - move promotion to knight
#+ 8 draw
#+ 16 check mate
#+ 32 

#128 - ilegal move
#129 - select new game
#130 - start game client white
#131 - start game client black
#132 - start game from this position

#133 - request board status1
REQ_STAT1 = 133
#134 - request board status2
REQ_STAT2 = 134
#135 - ready to play game
OK_TO_PLAY = 135

#136 transmit board status1
#137 -wait for status 2
#`138 transmit board status2
#139 - ready to start game
READY_TO_START = 139

vis = {'p': 17, 'n': 18 , 'b': 27, 'r': 28, 'q': 29, 'k': 22, 'P': 33, 'N': 34, 'B': 43, 'R': 44, 'Q': 45, 'K': 38} 

def capture1(data):
  for i in range(56, 24, -8):
    for j in range(0, 8):
      idx = i + j
      piece = board.piece_at(idx)
      if piece:
        num = vis[piece.symbol()]
      else:
        num = 0
      data.append(num)
  
  data.append(254)

def capture2(data):
  for i in range(24, -8, -8):
    for j in range(0, 8):
      idx = i + j
      piece = board.piece_at(idx)
      if piece:
        num = vis[piece.symbol()]
      else:
        num = 0
        
      data.append(num)

  enpass = board.ep_square
  if enpass:
    enpass = enpass & 7
  else:
    enpass = 0
        
  if board.has_kingside_castling_rights(True):
    enpass = enpass | 16
  if board.has_queenside_castling_rights(True):
    enpass = enpass | 32
  if board.has_kingside_castling_rights(False):
    enpass = enpass | 64
  if board.has_queenside_castling_rights(False):
    enpass = enpass | 128

  data.append(enpass)
  data.append(board.halfmove_clock)
  
  if board.turn:
    num = 32
  else:
    num = 16
  data.append(num)

  if client_white:
    num = 32
  else:
    num = 16
  data.append(num)
  data.append(254)

def transmit_board_stat1():
  data = [136]
  capture1(data)
  ser.write(data)

def transmit_board_stat2():
  data = [138]
  capture2(data)
  ser.write(data)

def game_status():
  if board.is_game_over(claim_draw = True):
    if board.is_checkmate():
      return 16
    else:
      return 8
  else:
    return 0

def do_move(move_from, move_to, promotion_to):
  LegalMove = board.legal_moves
  
  legal = False
  for jalan in LegalMove:
    jalan1 = jalan.from_square
    jalan2 = jalan.to_square
    if(jalan1 == move_from) and (jalan2 == move_to):
      legal = True
      break
    
  if legal:
    promosi = jalan.promotion
    
    if promosi:
      promotion_to = promotion_to & 71
      promotion_to = promotion_to - 65
      if promotion_to == 1:
        jalan.promotion = chess.QUEEN
      elif promotion_to == 2:
        jalan.promotion = chess.ROOK
      elif promotion_to == 3:
        jalan.promotion = chess.BISHOP
      elif promotion_to == 4:
        jalan.promotion = chess.KNIGHT
      
    board.push(jalan)
    print(board.ply())
    print(board)
    return True
  else:
    return False

def engine_run():
  try:
    move = book.choice(board, minimum_weight = 0).move
    print("book move is: ", BestMove)
  except:
    BestMove = engine.play(board, chess.engine.Limit(time = 5))
    move = BestMove.move
    print("engine move is:", move)

  dari = move.from_square
  ke = move.to_square
  print("dari =", dari)
  print("ke = ", ke)
  promosi = move.promotion

  promo_code = 0
  if promosi:
    move.promotion = chess.QUEEN
    promo_code = 1
  
  board.push(move)
  print(board.ply())
  print(board)
  print("\n\n")
  return dari, ke, promo_code

  

def eboard_handling():
    global last_move, command, select_new_game
    global ntransmit, max_transmit, delay, ndelay, client_white, host_white, device_err
    global iter, client_req, client_prev_from, client_prev_to, client_from, client_to

    iter = iter + 1
    print("iteration", iter)
    num_data = ser.in_waiting
    print("num data", num_data)
    print("last move = ", last_move)

    host_cmd = last_move[0]
    select_new_game = (host_cmd == 129)
    in_game = (host_cmd & 64) == 64
    client_turn = (client_white == board.turn)
    host_turn = not client_turn
    wait_to_play = (host_cmd == 130) or (host_cmd == 131) or (host_cmd == 139)
    game_ovr = ((host_cmd & 72) == 72) or ((host_cmd & 80) == 80)
    print("game over = ", game_ovr)
    select_new_game = (host_cmd == 129)
    board_capture = (host_cmd == 128) or (host_cmd == 132)
    wait_stat2 = (host_cmd == 137)

    print("client turn = ", client_turn)
    print("in game = ", in_game)

 
    if ((num_data % 6) == 0) and (num_data > 0):
      data = ser.read(num_data)
      #end of data
      client_to = data[num_data - 2]
      client_from = data[num_data - 3]
      client_prev_to = data[num_data - 4]
      client_prev_from = data[num_data - 5]
      client_req = data[num_data - 6]
      print("req = ", client_req)
      print("prev from = ", client_prev_from)
      print("prev to = ", client_prev_to)
      print("from = ", client_from)
      print("to = ", client_to)
      if (in_game and client_turn): ntransmit = ntransmit - 1
    elif delay > 0:
      print("delay = ", delay)
      delay = delay - 1
    elif wait_to_play or (in_game and client_turn) or game_ovr or board_capture:
      if ntransmit > max_transmit:
        device_err = True
        print("error board do not response !!!")
      else:
        ser.write(last_move)
        ntransmit = ntransmit + 1
        print("ntransmit kedua = ", ntransmit)
        delay = ndelay
    elif wait_stat2:
      if ntransmit > max_transmit:
        board_err = True
      else:
        transmit_board_stat1()
        ntransmit = ntransmit + 1
        delay = ndelay
    elif wait_to_play:
      if ntransmit > max_transmit:
        board_err = True
      else:
        transmit_board_stat2()
        ntransmit = ntransmit + 1
        delay = ndelay
  
    
    print("host command", host_cmd)

    if game_ovr:
      if client_req == READY_TO_START:
        last_move = [129, 64, 64, 64, 64, 256]
    elif select_new_game:
      print("command = ", command)
      if command == 1:
        #start game client white
        print("asu")
        last_move = [130, 64, 64, 64, 64, 254]
        client_white = True
        host_white = False
        board.reset()
        ser.write(last_move)
        ntransmit = 1
        delay = ndelay
      elif command == 2:
        #start game client black
        last_move = [131, 64, 64, 64, 64, 254]
        client_white = False
        host_white = True
        board.reset()
        ser.write(last_move)
        ntransmit = 1
        delay = ndelay
      elif command == 3:
        #start game from this position
        last_move[132, 64, 64, 64, 64, 254]
        ser.write(last_move)
        ntransmit = 1
        delay = ndelay
    elif wait_to_play:
      if client_req == OK_TO_PLAY:
        print("client ready to play")
        last_move = [65, 64, 64, 64, 64, 254]
        #check game status
        gstat = game_status()
        last_move[0] = last_move[0] + gstat
        ser.write(last_move)
        ntransmit = 1
        delay = ndelay
    elif in_game:
      if host_turn:
        #check game status
        gstat = game_status()
        if gstat != 0:
          #game_over
          gstat = gstat + 65
          last_move[0] =  gstat
          last_move[1] = last_move[3]
          last_move[2] = last_move[4]
          #game over, no move
          last_move[3] = 64
          last_move[4] = 64
          last_move[5] = 254
        else:
          move_from, move_to, promotion = engine_run()
          move_from = to_eboard(move_from)
          move_to = to_eboard(move_to)
          #new move has done, check game status
          gstat = game_status()
        
          gstat = gstat + 65 + promotion
          last_move[0] = gstat
          last_move[1] = last_move[3]
          last_move[2] = last_move[4]
          last_move[3] = move_from
          last_move[4] = move_to
          last_move[5] = 254
          ser.write(last_move)
          ntransmit = 1
          print("ntransmit yang pertama = ", ntransmit)
          delay = ndelay
      elif client_turn:
        if (client_prev_from == last_move[3]) and (client_prev_to == last_move[4]):
          if  not (client_from == 64):
            #client has moved
            move_from = to_eboard(client_from)
            move_to = to_eboard(client_to)
            legal_move = do_move(move_from, move_to, client_req)
            if not legal_move:
              #ilegal move
              last_move[0] = 128
              last_move[5] = 254
              ser.write(last_move)
              ntransmit = 1
              delay = ndelay
            else:
              #move has done
              last_move[1] = last_move[3]
              last_move[2] = last_move[4]
              last_move[3]= client_from
              last_move[4] = client_to
        elif (client_from != last_move[1]) or (client_to != last_move[2]):
          last_move[0] = 128
          last_move[5] = 254
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
    #ilegal move
    elif board_capture:
      #request board status1
      if client_req == REQ_STAT1:
        last_move[0] = 137
        transmit_board_stat1()
        ntransmit = 1
        delay = ndelay
    #wait request board status2
    elif host_cmd == wait_stat2:
      if client_req == REQ_STAT2:
        last_move[0] = 139
        transmit_board_stat2()
        ntransmit = 1
        delay = ndelay
   
    
        
      
        
#start game, client white
print("select options:")
print("0 quit")
print("1 play white")
print("2 play black")
command = int(input())
print("command = ",  command)

while not (command == 0):
  play_game = True
  eboard_handling()
  command = 0


  while play_game:
    eboard_handling()
    play_game = not (select_new_game) and not device_err
    time.sleep(0.5)

  print("select options:")
  print("0 quit")
  print("1 play white")
  print("2 play black")
  command = int(input())

    
print("program quit")  
engine.quit()
      


