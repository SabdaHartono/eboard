import chess.pgn
import chess.polyglot
import serial
import time

ser = serial.Serial('COM5', baudrate=9600)
book = chess.polyglot.open_reader("opening/performance.bin")
board = chess.Board()
print(board)
engine = chess.engine.SimpleEngine.popen_uci("c:\Program Files (x86)\Tarrasch\Engines\stockfish_8_x64")
pilih = {"Skill Level": 1}
engine.configure(pilih)
play_game = True
command = 1
select_new_game = True
last_move = [129, 136, 136, 136, 136, 254]
ntransmit = 0
max_transmit = 3
ndelay = 5
delay = ndelay
client_white =  True
host_white = False
device_err = False
client_req = 0
client_prev_from = 0
cleint_prev_to = 0
client_from = 0
client_to = 0

#eboard vis-light
eboard_piece = {'p': 17, 'n': 18 , 'b': 27, 'r': 28, 'q': 29, 'k': 22, 'P': 33, 'N': 34, 'B': 43, 'R': 44, 'Q': 45, 'K': 38} 

def to_eboard(square):
  return square ^ 56

def to_hostboard(square):
  return square ^ 56

def eboard_ep(ep_square):
  if ep_square:
    return ep_square & 7
  else:
    #code enpassant not valid
    return 15

def eboard_color(color):
  if color:
    return 32
  else:
    return 16

#eboard vis-micromax
#eboard_piece = {'p' : 18, 'n' : 19, 'b' : 21 , 'r' : 22, 'q' : 23, 'k' : 20, 'P' : 9, 'N' : 11, 'B' : 13, 'R' : 14, 'Q' : 15, 'K': 12}

#def to_eboard(square):
#  square = square ^ 56
#  square = square + (square & 56)
#  return square

#def to_hostboard(square):
#  square = square + (square & 7)
#  square = square >> 1
#  square = square ^ 56
#  return square

#def eboard_ep(ep_square):
# if ep_square:
#    return to_eboard(ep_square)
#  else:
    #code enpassant not valid
#    return 128
  
#def eboard_color(color):
#  if color:
#    return 8
#  else:
#    return 16

#host and client command
#0 - 63 move from, move to

#64 in game
#64 - no move (+0)
#65 - normal move (+1)
#66 - move promotion to knight (+2)
#67 - move promotion to bishop (+3)
#68 - move promotion to rook (+4)
#69 - move promotion to queen (+5)
#+ 8 draw
#+ 16 check mate
#+ 32 offer draw

# host command
#ilegal move
_ilegal_move = 128
#select new game
_select_ng = 129
#start game client white
_start_white = 130
#start game client black
_start_black = 131
#start game from this position
_start_this_pos = 132
#transmit board status1
_tx_board1 = 135
#wait for status 2
_wait_board2 = 137
#transmit board status2
_tx_board2 = 139
#wait_to_update
_wait_update = 141

#client_request
#request board status1
REQ_STAT1 = 134
#request board status2
REQ_STAT2 = 136
#ready to play game
OK_TO_PLAY = 138
#ready to start game
READY_TO_START = 140

          
def capture1(data):
  for i in range(56, 24, -8):
    for j in range(0, 8):
      idx = i + j
      piece = board.piece_at(idx)
      if piece:
        num = eboard_piece[piece.symbol()]
      else:
        num = 0
      data.append(num)

  #end of data
  data.append(254)

def capture2(data):
  for i in range(24, -8, -8):
    for j in range(0, 8):
      idx = i + j
      piece = board.piece_at(idx)
      if piece:
        num = eboard_piece[piece.symbol()]
      else:
        num = 0
        
      data.append(num)

  num = board.ep_square
  num = eboard_ep(num)
  data.append(num)
    
  cast = 0
  if board.has_kingside_castling_rights(True):
    cast = cast | 16
  if board.has_queenside_castling_rights(True):
    cast = cast | 32
  if board.has_kingside_castling_rights(False):
    cast = cast | 64
  if board.has_queenside_castling_rights(False):
    cast = cast | 128

  data.append(cast)
  data.append(board.halfmove_clock)

  num = eboard_color(board.turn)
  data.append(num)

  num = eboard_color(client_white)
  data.append(num)

  #end of data
  data.append(254)

def transmit_board_stat1():
  data = [_tx_board1]
  capture1(data)
  ser.write(data)

def transmit_board_stat2():
  data = [_tx_board2]
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
    if promotion_to == 1:
      promotion_to = None
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
    select_new_game = (host_cmd == _select_ng)
    in_game = (host_cmd & 64) == 64
    #print("info, in game = ", in_game)
    client_turn = (client_white == board.turn)
    #print("info, client turn = ", client_turn)
    host_turn = not client_turn
    wait_to_play = (host_cmd == _start_white) or (host_cmd == _start_black)
    game_ovr = ((host_cmd & 72) == 72) or ((host_cmd & 80) == 80)
    #print("game over = ", game_ovr)
    board_capture = (host_cmd == _start_this_pos)
    wait_stat2 = (host_cmd == _wait_board2)
    wait_to_update = (host_cmd == _wait_update)

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
        #print("request = ", client_req)
        #print("prev from = ", client_prev_from)
        #print("prev to = ", client_prev_to)
        #print("from = ", client_from)
        #print("to = ", client_to)
        tail = data[idx+5]
        if not (tail == 254):
          print("warning, data tail error, tail = ", tail)
        idx = idx + 6
        data_waiting = (num_data > idx)
        if (in_game and client_turn):
          ntransmit = ntransmit - 1

      elif delay > 0:
        #print("delay = ", delay)
        delay = delay - 1
      elif wait_to_play or (in_game and client_turn) or game_ovr or board_capture:
        if ntransmit > max_transmit:
          device_err = True
          print("error, board do not response !")
        else:
          #print("last move = ", last_move)
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
          last_move = [_select_ng, 136, 136, 136, 136, 254]
      elif select_new_game:
        #print("info command = ", command)
        if command == 1:
          #start game client white
          last_move = [_start_white, 136, 136, 136, 136, 254]
          client_white = True
          host_white = False
          board.reset()
          board.clear_stack()
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
        elif command == 2:
          #start game client black
          last_move = [_start_black, 136, 136, 136, 136, 254]
          client_white = False
          host_white = True
          board.reset()
          board.clear_stack()
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
        elif command == 3:
          #start game from this position, client white
          last_move = [_start_this_pos, 136, 136, 136, 136, 254]
          client_white = True
          host_white = False
          board.set_fen("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4")
          board.clear_stack()
          print(board)
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay
        elif command == 4:
          #start game from this position, client black
          last_move = [_start_this_pos, 136, 136, 136, 136, 254]
          client_white = False
          host_white = True
          board.set_fen("r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4")
          board.clear_stack()
          print(board)
          ser.write(last_move)
          ntransmit = 1
          delay = ndelay

      elif wait_to_play or wait_to_update:
        #print("info: wait to play or wait to update")
        if client_req == OK_TO_PLAY:
          #print("info, client ready to play")
          last_move = [65, 136, 136, 136, 136, 254]
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
            last_move[3] = 136
            last_move[4] = 136
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
          #print("this client turn")
          #print("last move in client turn", last_move)
          if (client_prev_from == last_move[3]) and (client_prev_to == last_move[4]):
            if  not (client_from == 136):
              #client has moved
              move_from = to_hostboard(client_from)
              move_to = to_hostboard(client_to)
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
             #print("info: alt1 = ", alt1)
             #print("info: alt2 = ", alt2)

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
          #print("client request board stat1")
          #host wait client to request board status 1
          last_move[0] = _wait_board2
          transmit_board_stat1()
          ntransmit = 1
          delay = ndelay
        #wait request board status2
      elif wait_stat2:
        if client_req == REQ_STAT2:
          #print("client request board stat2")
          #host in wait to play state, which is wait client to acknowledge ready to play
          last_move[0] = _wait_update
          transmit_board_stat2()
          ntransmit = 1
          delay = ndelay
    
   
    
        
      
        
#start game, client white
print("select options:")
print("0 quit")
print("1 play white")
print("2 play black")
print("3 some position, play white")
print("4 some position, play back")
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
  print("3 some position, play white")
  print("4 some position, play black")
  command = int(input())

    
print("program quit")  
engine.quit()
      


