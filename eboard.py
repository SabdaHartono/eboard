import chess.pgn
import chess.polyglot
import serial
import time

ser = serial.Serial('COM16', baudrate=9600)
book = chess.polyglot.open_reader("opening/performance.bin")
board = chess.Board()
print(board)
engine = chess.engine.SimpleEngine.popen_uci("c:\Program Files (x86)\Tarrasch\Engines\stockfish_8_x64")
pilih = {"Skill Level": 2}
engine.configure(pilih)
play_game = True
command = 1
select_new_game = True
last_move = [129, 64, 64, 64, 64, 254]
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

#host and client command
#0 - 63 move from, move to
#64 - no move
#65 - normal move
#66 - move promotion to knight
#67 - move promotion to bishop
#68 - move promotion to rook
#69 - move promotion to queen
#+ 8 draw
#+ 16 check mate
#+ 32 offer draw

# host command
#128 - ilegal move
#129 - select new game
#130 - start game client white
#131 - start game client black
#132 - start game from this position
#136 transmit board status1
#137 -wait for status 2
#138 transmit board status2
#140 wait_to_update

#client_request
#133 - request board status1
REQ_STAT1 = 133
#134 - request board status2
REQ_STAT2 = 134
#135 - ready to play game
OK_TO_PLAY = 135
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
    enpass = 15
        
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
  try:
    promotion_to = promotion_to & 7
    #if normal move
    if (promotion_to == 1){promotion_to = None}
    jalan = board.find_move(move_from, move_to, promotion_to);
    board.push(jalan)
    if not client_white:
      board1 = board.transform(chess.flip_vertical)
      board2 = board1.transform(chess.flip_horizontal)
      print(board2)
    else:
      print(board)
    print("FEN = " + board.fen())
    print("\n")
    return True
  except:
    print("error, ilegal move from client!")
    return False


  

def engine_run():
  try:
    move = book.choice(board, minimum_weight = 0).move
    print("book move is: ", move)
  except:
    BestMove = engine.play(board, chess.engine.Limit(time = 5))
    move = BestMove.move
    print("engine move is:", move)

  dari = move.from_square
  ke = move.to_square

  if move.promotion:
    promotion = move.promotion
  else:
    promotion = 1
  
  board.push(move)
  
  if not client_white:
    board1 = board.transform(chess.flip_vertical)
    board2 = board1.transform(chess.flip_horizontal)
    print(board2)
  else:
    print(board)

  print("FEN = " + board.fen())
  print("\n")
  return dari, ke, promotion

  

def eboard_handling():
    global last_move, command, select_new_game
    global ntransmit, max_transmit, delay, ndelay, client_white, host_white, device_err
    global client_req, client_prev_from, client_prev_to, client_from, client_to

    #print("last move = ", last_move)
    host_cmd = last_move[0]
    select_new_game = (host_cmd == 129)
    in_game = (host_cmd & 64) == 64
    client_turn = (client_white == board.turn)
    host_turn = not client_turn
    wait_to_play = (host_cmd == 130) or (host_cmd == 131) or (host_cmd == 139)
    game_ovr = ((host_cmd & 72) == 72) or ((host_cmd & 80) == 80)
    #print("game over = ", game_ovr)
    select_new_game = (host_cmd == 129)
    board_capture = (host_cmd == 128) or (host_cmd == 132)
    wait_stat2 = (host_cmd == 137)
    wait_to_update = (host_cmd == 140)

    #print("client turn = ", client_turn)
    #print("in game = ", in_game)

    num_data = ser.in_waiting
    #print("num data", num_data)

    data_waiting = True
    idx = 0
    data_avail = False
    if ((num_data % 6) == 0) and (num_data > 0):
      data = ser.read(num_data)
      data_avail = True
      
    while data_waiting:
      data_waiting = False
      if data_avail:
        client_req = data[idx]
        client_prev_from = data[idx+1]
        client_prev_to = data[idx+2]
        client_from = data[idx+3]
        client_to  = data[idx+4]
        tail = data[idx+5]
        if not (tail == 254):
          print("warning, data tail error, tail = ", tail)
        idx = idx + 6
        data_waiting = (num_data > idx)
        if (in_game and client_turn): ntransmit = ntransmit - 1
      elif delay > 0:
        #print("delay = ", delay)
        delay = delay - 1
      elif wait_to_play or (in_game and client_turn) or game_ovr or board_capture:
        if ntransmit > max_transmit:
          device_err = True
          print("error, board do not response !")
        else:
          ser.write(last_move)
          ntransmit = ntransmit + 1
          #print("info, next transmit = ", ntransmit)
          delay = ndelay
      elif wait_stat2:
        if ntransmit > max_transmit:
          board_err = True
          print("error, board do not response !")
        else:
          transmit_board_stat1()
          ntransmit = ntransmit + 1
          delay = ndelay
      elif wait_to_update:
        if ntransmit > max_transmit:
          board_err = True
          print("error, board do not respose !")
        else:
          transmit_board_stat2()
          ntransmit = ntransmit + 1
          delay = ndelay
  
    
      #print("info, host command", host_cmd)
      if game_ovr:
        if client_req == READY_TO_START:
          last_move = [129, 64, 64, 64, 64, 254]
      elif select_new_game:
        #print("info command = ", command)
        if command == 1:
          #start game client white
          last_move = [130, 64, 64, 64, 64, 254]
          client_white = True
          host_white = False
          board.reset()
          board.clear_stack()
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
        elif command == 2:
          #start game client black
          last_move = [131, 64, 64, 64, 64, 254]
          client_white = False
          host_white = True
          board.reset()
          board.clear_stack()
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
        elif command == 3:
          #start game from this position
          last_move = [132, 64, 64, 64, 64, 254]
          board.set_fen("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4")
          board.clear_stack()
          print(board)
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
      elif wait_to_play or wait_to_update:
        if client_req == OK_TO_PLAY:
          #print("info, client ready to play")
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
            gstat = gstat + 64 + promotion
            last_move[0] = gstat
            last_move[1] = last_move[3]
            last_move[2] = last_move[4]
            last_move[3] = move_from
            last_move[4] = move_to
            last_move[5] = 254
            ser.write(last_move)
            ntransmit = 1
            #print("info, first ntransmit = ", ntransmit)
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
                print("error, client move not legal")
                ser.write(last_move)
                ntransmit = 1
                delay = ndelay
              else:
                #move has done
                last_move[1] = last_move[3]
                last_move[2] = last_move[4]
                last_move[3]= client_from
                last_move[4] = client_to
          else:
             alt1 = (client_prev_from == last_move[1]) and (client_prev_to == last_move[2])
             alt1 = alt1 and (client_from == last_move[3]) and (client_to == last_move[4])
             alt2 = (client_from == last_move[1]) and (client_to == last_move[2])
             print("info: alt1 = ", alt1)
             print("info: alt2 = ", alt2)

             if (not alt1) and (not alt2):
              print("error on client move data!")
              last_move[0] = 128
              last_move[5] = 254
              ser.write(last_move)
              ntransmit = 1
              delay = ndelay
      elif board_capture:
        #request board status1
        if client_req == REQ_STAT1:
          print("client request board stat1")
          #host wait client to request board status 1
          last_move[0] = 137
          transmit_board_stat1()
          ntransmit = 1
          delay = ndelay
        #wait request board status2
      elif wait_stat2:
        if client_req == REQ_STAT2:
          print("client request board stat2")
          #host in wait to play state, which is wait client to acknowledge ready to play
          last_move[0] = 140
          transmit_board_stat2()
          ntransmit = 1
          delay = ndelay
    
   
    
        
      
        
#start game, client white
print("select options:")
print("0 quit")
print("1 play white")
print("2 play black")
print("3 play some position")
command = int(input())

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
  print("3 play some position")
  command = int(input())

    
print("program quit")  
engine.quit()
      


